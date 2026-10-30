"""Cible web RH volontairement hétérogène pour les tests de bout en bout."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from threading import Lock
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates


@dataclass(frozen=True, slots=True)
class DemoPersona:
    key: str
    email: str
    password: str
    portal_code: str
    display_name: str
    role: str
    departments: tuple[str, ...]


PERSONAS = {
    "manager-cactus": DemoPersona(
        key="manager-cactus",
        email="camille.cactus@example.test",
        password="Cactus!2026",
        portal_code="CACTUS-42",
        display_name="Camille Cactus",
        role="manager",
        departments=(
            "Astrologie salariale",
            "Paie quantique",
            "Recrutement de licornes",
        ),
    ),
    "agent-lama": DemoPersona(
        key="agent-lama",
        email="alex.lama@example.test",
        password="Lama!2026",
        portal_code="LAMA-7",
        display_name="Alex Lama",
        role="agent",
        departments=("Paie quantique",),
    ),
}

_RECORDS: dict[str, dict[str, str]] = {}
_RECORDS_LOCK = Lock()


def build_hr_demo_router(templates: Jinja2Templates) -> APIRouter:
    router = APIRouter(prefix="/demo/hr", tags=["cible-rh-demo"])

    @router.get("", include_in_schema=False)
    def index() -> RedirectResponse:
        return RedirectResponse("/demo/hr/login", status_code=303)

    @router.get("/login", response_class=HTMLResponse)
    def login_page(request: Request, error: str = "") -> HTMLResponse:
        return templates.TemplateResponse(
            request=request,
            name="hr_demo_login.html",
            context={"error": error},
        )

    @router.post("/login")
    def login(
        email: str = Form(),
        password: str = Form(),
        portal_code: str = Form(""),
    ) -> RedirectResponse:
        persona = next(
            (
                candidate
                for candidate in PERSONAS.values()
                if candidate.email == email.strip()
                and candidate.password == password
                and candidate.portal_code == portal_code.strip()
            ),
            None,
        )
        if persona is None:
            return RedirectResponse(
                "/demo/hr/login?error=Les+archives+cosmiques+refusent+ces+identifiants.",
                status_code=303,
            )
        response = RedirectResponse("/demo/hr/saisie", status_code=303)
        response.set_cookie(
            "hr_demo_session",
            persona.key,
            httponly=True,
            samesite="lax",
            max_age=3_600,
        )
        return response

    @router.post("/logout")
    def logout() -> RedirectResponse:
        response = RedirectResponse("/demo/hr/login", status_code=303)
        response.delete_cookie("hr_demo_session")
        return response

    @router.get("/saisie", response_class=HTMLResponse)
    def employee_form(request: Request) -> Response:
        persona = _persona_from_request(request)
        if persona is None:
            return RedirectResponse("/demo/hr/login", status_code=303)
        return _render_employee_form(
            templates,
            request,
            persona,
            parser_preview=False,
        )

    @router.get("/parser/saisie/{persona_key}", response_class=HTMLResponse)
    def parser_employee_form(
        request: Request,
        persona_key: str,
    ) -> HTMLResponse:
        persona = PERSONAS.get(persona_key, PERSONAS["agent-lama"])
        return _render_employee_form(
            templates,
            request,
            persona,
            parser_preview=True,
        )

    @router.post("/saisie")
    async def create_employee(request: Request) -> RedirectResponse:
        persona = _persona_from_request(request)
        if persona is None:
            return RedirectResponse("/demo/hr/login", status_code=303)
        form = await request.form()
        record_id = f"RH-{uuid4().hex[:8].upper()}"
        allowed_fields = (
            "employee_number",
            "first_name",
            "last_name",
            "work_email",
            "hire_date",
            "department",
            "contract_type",
            "animal_totem",
            "favorite_color",
            "energy_level",
            "remote_days",
            "skills",
            "manager_budget",
            "manager_comment",
        )
        record = {
            field: str(form.get(field) or "").strip()
            for field in allowed_fields
        }
        record.update(
            {
                "record_id": record_id,
                "created_by": persona.display_name,
                "created_by_role": persona.role,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        with _RECORDS_LOCK:
            _RECORDS[record_id] = record
        return RedirectResponse(
            f"/demo/hr/consultation/{record_id}",
            status_code=303,
        )

    @router.get(
        "/consultation/{record_id}",
        response_class=HTMLResponse,
    )
    def consultation(
        request: Request,
        record_id: str,
    ) -> Response:
        persona = _persona_from_request(request)
        if persona is None:
            return RedirectResponse("/demo/hr/login", status_code=303)
        with _RECORDS_LOCK:
            record = dict(_RECORDS.get(record_id, {}))
        if not record:
            return RedirectResponse("/demo/hr/saisie", status_code=303)
        return templates.TemplateResponse(
            request=request,
            name="hr_demo_consultation.html",
            context={
                "persona": persona,
                "record": record,
                "parser_preview": False,
            },
        )

    @router.get("/parser/consultation", response_class=HTMLResponse)
    def parser_consultation(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(
            request=request,
            name="hr_demo_consultation.html",
            context={
                "persona": PERSONAS["manager-cactus"],
                "record": _sample_record(),
                "parser_preview": True,
            },
        )

    return router


def reset_hr_demo_records() -> None:
    """Réinitialise seulement les données éphémères de la cible de test."""

    with _RECORDS_LOCK:
        _RECORDS.clear()


def _persona_from_request(request: Request) -> DemoPersona | None:
    return PERSONAS.get(request.cookies.get("hr_demo_session", ""))


def _render_employee_form(
    templates: Jinja2Templates,
    request: Request,
    persona: DemoPersona,
    *,
    parser_preview: bool,
) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="hr_demo_form.html",
        context={
            "persona": persona,
            "parser_preview": parser_preview,
        },
    )


def _sample_record() -> dict[str, Any]:
    return {
        "record_id": "RH-PREVIEW",
        "employee_number": "EMP-NEB-042",
        "first_name": "Zoé",
        "last_name": "Nébuleuse",
        "work_email": "zoe.nebuleuse@example.test",
        "hire_date": "2026-09-01",
        "department": "Recrutement de licornes",
        "contract_type": "CDI intersidéral",
        "animal_totem": "Poulpe comptable",
        "favorite_color": "#ff4fd8",
        "energy_level": "87",
        "remote_days": "3",
        "skills": "Python, négociation avec les dragons",
        "manager_budget": "42000",
        "manager_comment": "Installer un hamac ergonomique homologué.",
        "created_by": "Camille Cactus",
        "created_by_role": "manager",
        "created_at": "2026-07-30T08:00:00+00:00",
    }
