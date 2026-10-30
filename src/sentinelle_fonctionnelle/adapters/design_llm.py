"""Adaptateur HTTP borné des LLM de conception compatibles chat-completions."""

from __future__ import annotations

import json
from collections.abc import Mapping
from os import environ
from time import sleep
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from sentinelle_fonctionnelle.domain import LLMAccessProfile


class DesignLLMError(RuntimeError):
    """L'appel au fournisseur n'a pas produit une réponse exploitable."""


class ConfiguredDesignLLM:
    """Résout les secrets tardivement et exige une réponse JSON fermée."""

    _DEFAULT_URLS = {
        "openai": "https://api.openai.com/v1",
        "anthropic": "https://api.anthropic.com/v1",
        "mistral": "https://api.mistral.ai/v1",
    }
    _SUPPORTED = {"openai", "openai-compatible", "ollama", "mistral"}

    def __init__(
        self,
        *,
        environment: Mapping[str, str] | None = None,
        opener: object = urlopen,
    ) -> None:
        self._environment = environment if environment is not None else environ
        self._opener = opener

    def complete(
        self,
        *,
        profile: LLMAccessProfile,
        request: dict[str, Any],
    ) -> Mapping[str, Any]:
        base_url, headers = self._connection_parameters(profile)
        is_connectivity_probe = request.get("prompt_version") == "connectivity-v1"
        payload: dict[str, Any] = {
            "model": profile.model,
            "temperature": 0.1,
            "max_tokens": 256 if is_connectivity_probe else 4096,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Tu assistes la conception d’un cas de test. "
                        "Réponds uniquement avec l’objet JSON demandé. "
                        "Ne confirme aucun fait, contrôle ou résultat."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        request,
                        ensure_ascii=False,
                        separators=(",", ":"),
                    ),
                },
            ],
        }
        if profile.provider == "ollama":
            # Qwen3.6 expose le raisonnement via l'API compatible OpenAI.
            # La conception attend ici le contrat JSON, pas les traces de pensée.
            payload["reasoning_effort"] = "none"
        body = json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        raw = self._request(
            profile=profile,
            request=Request(
                base_url.rstrip("/") + "/chat/completions",
                data=body,
                headers=headers,
                method="POST",
            ),
        )
        return _response_content(raw)

    def generate_code(
        self,
        *,
        profile: LLMAccessProfile,
        prompt: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        """Adresse au modèle les messages déjà audités du prompt de code."""

        raw_messages = prompt.get("messages")
        if not isinstance(raw_messages, list) or len(raw_messages) != 2:
            raise DesignLLMError(
                "Le prompt de génération doit contenir deux messages audités."
            )
        messages: list[dict[str, str]] = []
        for index, value in enumerate(raw_messages):
            expected_role = "system" if index == 0 else "user"
            if not isinstance(value, Mapping):
                raise DesignLLMError("Un message de génération est invalide.")
            role = value.get("role")
            content = value.get("content")
            if (
                role != expected_role
                or not isinstance(content, str)
                or not content.strip()
            ):
                raise DesignLLMError(
                    "Les rôles ou contenus du prompt de génération sont invalides."
                )
            messages.append({"role": expected_role, "content": content})

        base_url, headers = self._connection_parameters(profile)
        payload: dict[str, Any] = {
            "model": profile.model,
            "temperature": 0,
            "max_tokens": 32_768,
            "response_format": {"type": "json_object"},
            "messages": messages,
        }
        if profile.provider == "ollama":
            payload["reasoning_effort"] = "none"
        raw = self._request(
            profile=profile,
            request=Request(
                base_url.rstrip("/") + "/chat/completions",
                data=json.dumps(
                    payload,
                    ensure_ascii=False,
                    separators=(",", ":"),
                ).encode("utf-8"),
                headers=headers,
                method="POST",
            ),
        )
        return _response_content(raw)

    def probe(self, *, profile: LLMAccessProfile) -> Mapping[str, Any]:
        """Vérifie le serveur et la présence du modèle sans le charger."""

        base_url, headers = self._connection_parameters(profile)
        if profile.provider == "ollama":
            origin = base_url.rstrip("/")
            if origin.endswith("/v1"):
                origin = origin[:-3]
            version_payload = _json_object(
                self._request(
                    profile=profile,
                    request=Request(
                        origin + "/api/version",
                        headers=headers,
                        method="GET",
                    ),
                )
            )
            models_payload = _json_object(
                self._request(
                    profile=profile,
                    request=Request(
                        origin + "/api/tags",
                        headers=headers,
                        method="GET",
                    ),
                )
            )
            model_ids = {
                identifier
                for item in models_payload.get("models", [])
                if isinstance(item, Mapping)
                for identifier in (item.get("name"), item.get("model"))
                if isinstance(identifier, str)
            }
            return {
                "engine": "Ollama",
                "engine_version": str(version_payload.get("version", "inconnue")),
                "model_available": profile.model in model_ids,
            }

        models_payload = _json_object(
            self._request(
                profile=profile,
                request=Request(
                    base_url.rstrip("/") + "/models",
                    headers=headers,
                    method="GET",
                ),
            )
        )
        model_ids = {
            item.get("id")
            for item in models_payload.get("data", [])
            if isinstance(item, Mapping) and isinstance(item.get("id"), str)
        }
        return {
            "engine": profile.provider,
            "engine_version": "non communiqué",
            "model_available": profile.model in model_ids,
        }

    def list_models(self, *, profile: LLMAccessProfile) -> tuple[str, ...]:
        """Retourne le catalogue exposé par l’URL du profil, sans inférence."""

        base_url, headers = self._model_catalog_connection_parameters(profile)
        if profile.provider == "ollama":
            origin = base_url.rstrip("/")
            if origin.endswith("/v1"):
                origin = origin[:-3]
            raw = self._request(
                profile=profile,
                request=Request(
                    origin + "/api/tags",
                    headers=headers,
                    method="GET",
                ),
            )
            return _model_identifiers(raw, collection_key="models")

        raw = self._request(
            profile=profile,
            request=Request(
                base_url.rstrip("/") + "/models",
                headers=headers,
                method="GET",
            ),
        )
        return _model_identifiers(raw, collection_key="data")

    def _model_catalog_connection_parameters(
        self,
        profile: LLMAccessProfile,
    ) -> tuple[str, dict[str, str]]:
        if profile.provider in self._SUPPORTED:
            return self._connection_parameters(profile)
        if profile.provider not in {"anthropic", "azure-openai"}:
            raise DesignLLMError(
                f"Le fournisseur {profile.provider} ne possède pas de "
                "catalogue de modèles pris en charge."
            )
        base_url = profile.base_url or self._DEFAULT_URLS.get(
            profile.provider,
            "",
        )
        if not base_url:
            raise DesignLLMError("L’URL du fournisseur LLM est absente.")
        key = self._environment.get(profile.api_key_environment, "")
        if not key:
            raise DesignLLMError(
                "La variable d’environnement "
                f"{profile.api_key_environment} est absente."
            )
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "SentinelleFonctionnelle-design/1",
        }
        if profile.provider == "anthropic":
            headers["x-api-key"] = key
            headers["anthropic-version"] = "2023-06-01"
        else:
            headers["api-key"] = key
        return base_url, headers

    def chat(self, *, profile: LLMAccessProfile, message: str) -> str:
        """Envoie un message libre borné et retourne le texte du modèle."""

        base_url, headers = self._connection_parameters(profile)
        payload: dict[str, Any] = {
            "model": profile.model,
            "temperature": 0.2,
            "max_tokens": 1024,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Tu es l’assistant de l’équipe de test. "
                        "Réponds clairement et sans révéler de secret."
                    ),
                },
                {"role": "user", "content": message},
            ],
        }
        if profile.provider == "ollama":
            payload["reasoning_effort"] = "none"
        raw = self._request(
            profile=profile,
            request=Request(
                base_url.rstrip("/") + "/chat/completions",
                data=json.dumps(
                    payload,
                    ensure_ascii=False,
                    separators=(",", ":"),
                ).encode("utf-8"),
                headers=headers,
                method="POST",
            ),
        )
        return _response_text(raw)

    def _connection_parameters(
        self,
        profile: LLMAccessProfile,
    ) -> tuple[str, dict[str, str]]:
        if not profile.enabled:
            raise DesignLLMError(
                f"Le profil LLM {profile.reference} est désactivé."
            )
        if profile.provider not in self._SUPPORTED:
            raise DesignLLMError(
                f"Le fournisseur {profile.provider} ne possède pas encore "
                "d’adaptateur de dialogue."
            )
        base_url = profile.base_url or self._DEFAULT_URLS.get(
            profile.provider,
            "",
        )
        if not base_url:
            raise DesignLLMError("L’URL du fournisseur LLM est absente.")
        key = ""
        if profile.api_key_environment:
            key = self._environment.get(profile.api_key_environment, "")
            if not key:
                raise DesignLLMError(
                    "La variable d’environnement "
                    f"{profile.api_key_environment} est absente."
                )
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "SentinelleFonctionnelle-design/1",
        }
        if key:
            headers["Authorization"] = f"Bearer {key}"
        if profile.organization_environment:
            organization = self._environment.get(
                profile.organization_environment,
                "",
            )
            if organization:
                headers["OpenAI-Organization"] = organization
        return base_url, headers

    def _request(self, *, profile: LLMAccessProfile, request: Request) -> bytes:
        last_error = "erreur inconnue"
        for attempt in range(profile.max_retries + 1):
            try:
                response = self._opener(
                    request,
                    timeout=profile.request_timeout_seconds,
                )
                try:
                    raw = response.read(2 * 1024 * 1024 + 1)
                finally:
                    close = getattr(response, "close", None)
                    if callable(close):
                        close()
                if len(raw) > 2 * 1024 * 1024:
                    raise DesignLLMError(
                        "La réponse LLM dépasse la limite de 2 Mio."
                    )
                return raw
            except HTTPError as error:
                last_error = _http_error_detail(error)
            except (URLError, OSError, ValueError) as error:
                last_error = str(error)
            if attempt < profile.max_retries:
                sleep(min(0.25 * (attempt + 1), 1))
        raise DesignLLMError(
            "Le fournisseur LLM n’a pas répondu correctement : "
            f"{last_error}."
        )


def _response_content(raw: bytes) -> Mapping[str, Any]:
    try:
        envelope = json.loads(raw.decode("utf-8"))
        content = envelope["choices"][0]["message"]["content"]
        parsed = json.loads(content)
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
        KeyError,
        IndexError,
        TypeError,
    ) as error:
        raise DesignLLMError(
            "Le fournisseur LLM a retourné une enveloppe ou un JSON invalide."
        ) from error
    if not isinstance(parsed, Mapping):
        raise DesignLLMError("La réponse LLM doit être un objet JSON.")
    return parsed


def _response_text(raw: bytes) -> str:
    try:
        envelope = json.loads(raw.decode("utf-8"))
        content = envelope["choices"][0]["message"]["content"]
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
        KeyError,
        IndexError,
        TypeError,
    ) as error:
        raise DesignLLMError(
            "Le fournisseur LLM a retourné une enveloppe invalide."
        ) from error
    if not isinstance(content, str) or not content.strip():
        raise DesignLLMError("Le fournisseur LLM a retourné une réponse vide.")
    return content.strip()


def _json_object(raw: bytes) -> Mapping[str, Any]:
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DesignLLMError("Le fournisseur a retourné un JSON invalide.") from error
    if not isinstance(payload, Mapping):
        raise DesignLLMError("La réponse du fournisseur doit être un objet JSON.")
    return payload


def _model_identifiers(
    raw: bytes,
    *,
    collection_key: str,
) -> tuple[str, ...]:
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DesignLLMError(
            "Le catalogue des modèles contient un JSON invalide."
        ) from error
    if isinstance(payload, Mapping):
        values = payload.get(collection_key, [])
    else:
        values = payload
    if not isinstance(values, list):
        raise DesignLLMError(
            "Le fournisseur n’a pas retourné une liste de modèles."
        )
    identifiers = {
        identifier.strip()
        for item in values[:2_000]
        if isinstance(item, Mapping)
        for identifier in (item.get("id"), item.get("name"), item.get("model"))
        if isinstance(identifier, str)
        and identifier.strip()
        and len(identifier.strip()) <= 512
    }
    if not identifiers:
        raise DesignLLMError(
            "Le fournisseur n’a retourné aucun identifiant de modèle."
        )
    return tuple(sorted(identifiers, key=str.casefold))


def _http_error_detail(error: HTTPError) -> str:
    detail = f"HTTP {error.code}"
    try:
        raw = error.read(64 * 1024)
        payload = json.loads(raw.decode("utf-8"))
        candidate: object = payload.get("error", payload)
        if isinstance(candidate, Mapping):
            candidate = candidate.get("message", candidate.get("detail", candidate))
        if isinstance(candidate, str) and candidate.strip():
            detail += f" — {candidate.strip()[:1200]}"
    except (AttributeError, UnicodeDecodeError, json.JSONDecodeError):
        pass
    return detail
