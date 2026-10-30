"""Routeur configuration de l'interface locale."""

from __future__ import annotations

import os
from dataclasses import replace
from time import perf_counter

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from sentinelle_fonctionnelle.adapters.design_llm import DesignLLMError
from sentinelle_fonctionnelle.application import (
    CODE_GENERATION_SKILLS,
)
from sentinelle_fonctionnelle.application.design_assistant import (
    build_connectivity_request,
)
from sentinelle_fonctionnelle.domain import (
    SUPPORTED_EVIDENCE_MODES,
    SUPPORTED_FRAMEWORKS,
    SUPPORTED_GENERATION_SKILLS,
    SUPPORTED_LANGUAGES,
    SUPPORTED_OVERWRITE_POLICIES,
    SUPPORTED_PROVIDERS,
    SUPPORTED_VALIDATION_STEPS,
    DesignAssistantResponse,
    GenerationProfileError,
    LLMAccessProfile,
)
from sentinelle_fonctionnelle.web import route_support as support
from sentinelle_fonctionnelle.web.composition import WebServices


def build_configuration_router(
    services: WebServices,
    templates: Jinja2Templates,
) -> APIRouter:
    """Construit le routeur configuration avec ses dépendances explicites."""

    configuration_router = APIRouter(tags=["configuration"])
    test_approach_catalog = services.test_approaches
    generation_profile_catalog = services.generation_profiles

    @configuration_router.get(
        "/configuration/test-approaches", response_class=HTMLResponse
    )
    def test_approach_configuration(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(
            request=request,
            name="test_approaches.html",
            context={
                "profiles": test_approach_catalog.current_profiles(
                    include_disabled=True
                ),
                "catalog_path": test_approach_catalog.path,
            },
        )

    @configuration_router.post("/configuration/test-approaches")
    def create_test_approach(
        profile_id: str = Form(),
        name: str = Form(),
        description: str = Form(),
        test_levels: str = Form(),
        test_types: str = Form(),
        test_design_techniques: str = Form(),
        risk_based: bool = Form(False),
        automation_strategy: str = Form(),
        evidence_requirements: str = Form(""),
        generation_instructions: str = Form(),
        enabled: bool = Form(False),
    ) -> RedirectResponse:
        profile = test_approach_catalog.create(
            profile_id=profile_id,
            name=name,
            description=description,
            test_levels=support.line_values(test_levels),
            test_types=support.line_values(test_types),
            test_design_techniques=support.line_values(test_design_techniques),
            risk_based=risk_based,
            automation_strategy=automation_strategy,
            evidence_requirements=support.line_values(evidence_requirements),
            generation_instructions=support.line_values(generation_instructions),
            enabled=enabled,
        )
        return RedirectResponse(
            f"/configuration/test-approaches#approach-{profile.id}",
            status_code=303,
        )

    @configuration_router.post("/configuration/test-approaches/{profile_id}")
    def update_test_approach(
        profile_id: str,
        name: str = Form(),
        description: str = Form(),
        test_levels: str = Form(),
        test_types: str = Form(),
        test_design_techniques: str = Form(),
        risk_based: bool = Form(False),
        automation_strategy: str = Form(),
        evidence_requirements: str = Form(""),
        generation_instructions: str = Form(),
        enabled: bool = Form(False),
    ) -> RedirectResponse:
        profile = test_approach_catalog.update(
            profile_id,
            name=name,
            description=description,
            test_levels=support.line_values(test_levels),
            test_types=support.line_values(test_types),
            test_design_techniques=support.line_values(test_design_techniques),
            risk_based=risk_based,
            automation_strategy=automation_strategy,
            evidence_requirements=support.line_values(evidence_requirements),
            generation_instructions=support.line_values(generation_instructions),
            enabled=enabled,
        )
        return RedirectResponse(
            f"/configuration/test-approaches#approach-{profile.id}",
            status_code=303,
        )

    def render_generation_configuration(
        request: Request,
        configuration_section: str,
    ) -> HTMLResponse:
        access_profiles = generation_profile_catalog.current_llm_access(
            include_disabled=True,
        )
        generation_profiles = generation_profile_catalog.current_code_generation(
            include_disabled=True,
        )
        environment_status = {
            profile.reference: (
                not profile.api_key_environment
                or profile.api_key_environment in os.environ
            )
            for profile in access_profiles
        }
        return templates.TemplateResponse(
            request=request,
            name="generation_configuration.html",
            context={
                "access_profiles": access_profiles,
                "all_access_versions": (generation_profile_catalog.llm_access_profiles),
                "generation_profiles": generation_profiles,
                "environment_status": environment_status,
                "catalog_path": generation_profile_catalog.path,
                "providers": SUPPORTED_PROVIDERS,
                "languages": SUPPORTED_LANGUAGES,
                "frameworks": SUPPORTED_FRAMEWORKS,
                "evidence_modes": SUPPORTED_EVIDENCE_MODES,
                "overwrite_policies": SUPPORTED_OVERWRITE_POLICIES,
                "validation_steps": SUPPORTED_VALIDATION_STEPS,
                "generation_skill_references": SUPPORTED_GENERATION_SKILLS,
                "generation_skill_catalog": CODE_GENERATION_SKILLS,
                "configuration_section": configuration_section,
            },
        )

    @configuration_router.get("/configuration/generation")
    def legacy_generation_configuration() -> RedirectResponse:
        """Conserve les anciens favoris sans maintenir un écran ambigu."""
        return RedirectResponse("/configuration/llm-access", status_code=307)

    @configuration_router.get("/configuration/llm-access", response_class=HTMLResponse)
    def llm_access_configuration(request: Request) -> HTMLResponse:
        return render_generation_configuration(request, "llm")

    @configuration_router.get(
        "/configuration/code-generation", response_class=HTMLResponse
    )
    def code_generation_configuration(request: Request) -> HTMLResponse:
        return render_generation_configuration(request, "code")

    @configuration_router.post("/configuration/llm-access-profiles")
    def create_llm_access_profile(
        profile_id: str = Form(),
        name: str = Form(),
        provider: str = Form(),
        base_url: str = Form(""),
        model: str = Form(),
        api_key_environment: str = Form(""),
        organization_environment: str = Form(""),
        request_timeout_seconds: int = Form(60),
        max_retries: int = Form(2),
        enabled: bool = Form(False),
    ) -> RedirectResponse:
        profile = generation_profile_catalog.create_llm_access(
            profile_id=profile_id,
            name=name,
            provider=provider,
            base_url=base_url,
            model=model,
            api_key_environment=api_key_environment,
            organization_environment=organization_environment,
            request_timeout_seconds=request_timeout_seconds,
            max_retries=max_retries,
            enabled=enabled,
        )
        return RedirectResponse(
            f"/configuration/llm-access#llm-{profile.id}",
            status_code=303,
        )

    @configuration_router.post("/configuration/llm-access-profiles/{profile_id}")
    def update_llm_access_profile(
        profile_id: str,
        name: str = Form(),
        provider: str = Form(),
        base_url: str = Form(""),
        model: str = Form(),
        api_key_environment: str = Form(""),
        organization_environment: str = Form(""),
        request_timeout_seconds: int = Form(60),
        max_retries: int = Form(2),
        enabled: bool = Form(False),
    ) -> RedirectResponse:
        profile = generation_profile_catalog.update_llm_access(
            profile_id,
            name=name,
            provider=provider,
            base_url=base_url,
            model=model,
            api_key_environment=api_key_environment,
            organization_environment=organization_environment,
            request_timeout_seconds=request_timeout_seconds,
            max_retries=max_retries,
            enabled=enabled,
        )
        return RedirectResponse(
            f"/configuration/llm-access#llm-{profile.id}",
            status_code=303,
        )

    @configuration_router.post("/configuration/llm-models")
    def list_llm_models(
        request: Request,
        provider: str = Form(),
        base_url: str = Form(""),
        api_key_environment: str = Form(""),
        organization_environment: str = Form(""),
        request_timeout_seconds: int = Form(30),
    ) -> JSONResponse:
        try:
            discovery_profile = LLMAccessProfile(
                id="model-catalog",
                version=1,
                name="Découverte des modèles",
                provider=provider,
                base_url=base_url.strip().rstrip("/"),
                model="catalogue-only",
                api_key_environment=api_key_environment.strip(),
                organization_environment=organization_environment.strip(),
                request_timeout_seconds=max(
                    1,
                    min(request_timeout_seconds, 30),
                ),
                max_retries=0,
                enabled=True,
            )
        except GenerationProfileError as error:
            return JSONResponse(
                {"status": "error", "detail": str(error)},
                status_code=400,
            )

        started_at = perf_counter()
        try:
            models = request.app.state.design_llm.list_models(
                profile=discovery_profile,
            )
        except DesignLLMError as error:
            return JSONResponse(
                {"status": "error", "detail": str(error)},
                status_code=502,
            )
        return JSONResponse(
            {
                "status": "ok",
                "provider": provider,
                "base_url": discovery_profile.base_url,
                "models": list(models),
                "count": len(models),
                "duration_ms": round((perf_counter() - started_at) * 1_000),
            }
        )

    @configuration_router.post(
        "/configuration/llm-access-profiles/{profile_id}"
        "/versions/{version}/connectivity"
    )
    def test_llm_access_connectivity(
        request: Request,
        profile_id: str,
        version: int,
    ) -> JSONResponse:
        profile = generation_profile_catalog.get_llm_access(
            profile_id,
            version,
        )
        started_at = perf_counter()
        try:
            probe = request.app.state.design_llm.probe(
                # Un profil doit pouvoir être contrôlé avant son activation.
                profile=replace(profile, enabled=True),
            )
        except DesignLLMError as error:
            return JSONResponse(
                {"status": "error", "detail": str(error)},
                status_code=502,
            )
        return JSONResponse(
            {
                "status": ("ok" if probe.get("model_available") else "warning"),
                "profile": profile.reference,
                "provider": profile.provider,
                "model": profile.model,
                **probe,
                "duration_ms": round((perf_counter() - started_at) * 1_000),
            }
        )

    @configuration_router.post(
        "/configuration/llm-access-profiles/{profile_id}"
        "/versions/{version}/structured-test"
    )
    def test_llm_structured_inference(
        request: Request,
        profile_id: str,
        version: int,
    ) -> JSONResponse:
        profile = generation_profile_catalog.get_llm_access(
            profile_id,
            version,
        )
        started_at = perf_counter()
        try:
            raw_response = request.app.state.design_llm.complete(
                profile=replace(profile, enabled=True),
                request=build_connectivity_request(),
            )
            response = DesignAssistantResponse.from_mapping(raw_response)
        except (DesignLLMError, ValueError, TypeError) as error:
            return JSONResponse(
                {"status": "error", "detail": str(error)},
                status_code=502,
            )
        return JSONResponse(
            {
                "status": "ok",
                "profile": profile.reference,
                "model": profile.model,
                "structured_json": True,
                "questions": len(response.questions),
                "operations": len(response.operations),
                "duration_ms": round((perf_counter() - started_at) * 1_000),
            }
        )

    @configuration_router.post(
        "/configuration/llm-access-profiles/{profile_id}/versions/{version}/interact"
    )
    def interact_with_llm(
        request: Request,
        profile_id: str,
        version: int,
        message: str = Form(),
    ) -> JSONResponse:
        normalized_message = message.strip()
        if not normalized_message:
            return JSONResponse(
                {"status": "error", "detail": "Le message est vide."},
                status_code=400,
            )
        if len(normalized_message) > 4_000:
            return JSONResponse(
                {
                    "status": "error",
                    "detail": "Le message dépasse la limite de 4 000 caractères.",
                },
                status_code=400,
            )
        profile = generation_profile_catalog.get_llm_access(
            profile_id,
            version,
        )
        started_at = perf_counter()
        try:
            answer = request.app.state.design_llm.chat(
                profile=replace(profile, enabled=True),
                message=normalized_message,
            )
        except DesignLLMError as error:
            return JSONResponse(
                {"status": "error", "detail": str(error)},
                status_code=502,
            )
        return JSONResponse(
            {
                "status": "ok",
                "profile": profile.reference,
                "model": profile.model,
                "answer": answer,
                "duration_ms": round((perf_counter() - started_at) * 1_000),
            }
        )

    @configuration_router.post("/configuration/code-generation-profiles")
    def create_code_generation_profile(
        profile_id: str = Form(),
        name: str = Form(),
        llm_profile: str = Form(),
        language: str = Form(),
        framework: str = Form(),
        output_root: str = Form(),
        test_file_pattern: str = Form(),
        page_object_pattern: str = Form(),
        use_page_objects: bool = Form(False),
        include_comments: bool = Form(False),
        evidence_mode: str = Form(),
        overwrite_policy: str = Form(),
        validation_steps: str = Form(),
        generation_instructions: str = Form(),
        generation_skills: str = Form(
            "functional-test-generation@1\ngenerate-python-playwright-code@1"
        ),
        max_generated_files: int = Form(20),
        enabled: bool = Form(False),
    ) -> RedirectResponse:
        profile = generation_profile_catalog.create_code_generation(
            profile_id=profile_id,
            name=name,
            llm_profile=llm_profile,
            language=language,
            framework=framework,
            output_root=output_root,
            test_file_pattern=test_file_pattern,
            page_object_pattern=page_object_pattern,
            use_page_objects=use_page_objects,
            include_comments=include_comments,
            evidence_mode=evidence_mode,
            overwrite_policy=overwrite_policy,
            validation_steps=support.line_values(validation_steps),
            generation_instructions=support.line_values(generation_instructions),
            generation_skills=support.line_values(generation_skills),
            max_generated_files=max_generated_files,
            enabled=enabled,
        )
        return RedirectResponse(
            f"/configuration/code-generation#generation-{profile.id}",
            status_code=303,
        )

    @configuration_router.post("/configuration/code-generation-profiles/{profile_id}")
    def update_code_generation_profile(
        profile_id: str,
        name: str = Form(),
        llm_profile: str = Form(),
        language: str = Form(),
        framework: str = Form(),
        output_root: str = Form(),
        test_file_pattern: str = Form(),
        page_object_pattern: str = Form(),
        use_page_objects: bool = Form(False),
        include_comments: bool = Form(False),
        evidence_mode: str = Form(),
        overwrite_policy: str = Form(),
        validation_steps: str = Form(),
        generation_instructions: str = Form(),
        generation_skills: str = Form(
            "functional-test-generation@1\ngenerate-python-playwright-code@1"
        ),
        max_generated_files: int = Form(20),
        enabled: bool = Form(False),
    ) -> RedirectResponse:
        profile = generation_profile_catalog.update_code_generation(
            profile_id,
            name=name,
            llm_profile=llm_profile,
            language=language,
            framework=framework,
            output_root=output_root,
            test_file_pattern=test_file_pattern,
            page_object_pattern=page_object_pattern,
            use_page_objects=use_page_objects,
            include_comments=include_comments,
            evidence_mode=evidence_mode,
            overwrite_policy=overwrite_policy,
            validation_steps=support.line_values(validation_steps),
            generation_instructions=support.line_values(generation_instructions),
            generation_skills=support.line_values(generation_skills),
            max_generated_files=max_generated_files,
            enabled=enabled,
        )
        return RedirectResponse(
            f"/configuration/code-generation#generation-{profile.id}",
            status_code=303,
        )

    return configuration_router
