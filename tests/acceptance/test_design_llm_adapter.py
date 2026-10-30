"""Contrat HTTP borné de l’adaptateur LLM de conception."""

from __future__ import annotations

import json
from io import BytesIO
import unittest
from urllib.error import HTTPError

from sentinelle_fonctionnelle.adapters.design_llm import (
    ConfiguredDesignLLM,
    DesignLLMError,
)
from sentinelle_fonctionnelle.domain import LLMAccessProfile


class _Response:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload
        self.closed = False

    def read(self, size: int) -> bytes:
        return json.dumps(self.payload).encode("utf-8")

    def close(self) -> None:
        self.closed = True


class DesignLLMAdapterAcceptanceTests(unittest.TestCase):
    def test_secret_is_resolved_only_in_header_and_response_is_closed(self) -> None:
        calls: list[tuple[object, int, _Response]] = []

        def opener(request: object, *, timeout: int) -> _Response:
            response = _Response(
                {
                    "choices": [
                        {
                            "message": {
                                "content": json.dumps(
                                    {
                                        "schema_version": 1,
                                        "questions": [],
                                        "operations": [],
                                    }
                                )
                            }
                        }
                    ]
                }
            )
            calls.append((request, timeout, response))
            return response

        adapter = ConfiguredDesignLLM(
            environment={"DESIGN_API_KEY": "secret-value"},
            opener=opener,
        )
        result = adapter.complete(
            profile=self._profile(),
            request={"schema_version": 1, "current_draft": {"objective": ""}},
        )

        self.assertEqual(1, result["schema_version"])
        request, timeout, response = calls[0]
        self.assertEqual("https://llm.example.invalid/v1/chat/completions", request.full_url)
        self.assertEqual(12, timeout)
        self.assertEqual("Bearer secret-value", request.headers["Authorization"])
        self.assertNotIn(b"secret-value", request.data)
        self.assertTrue(response.closed)

    def test_ollama_probe_disables_reasoning_and_limits_the_response(self) -> None:
        calls: list[object] = []

        def opener(request: object, *, timeout: int) -> _Response:
            calls.append(request)
            return _Response(
                {
                    "choices": [
                        {
                            "message": {
                                "content": json.dumps(
                                    {
                                        "schema_version": 1,
                                        "questions": [],
                                        "operations": [],
                                    }
                                )
                            }
                        }
                    ]
                }
            )

        adapter = ConfiguredDesignLLM(environment={}, opener=opener)
        adapter.complete(
            profile=LLMAccessProfile(
                id="ollama-qwen",
                version=1,
                name="Ollama Qwen",
                provider="ollama",
                base_url="http://127.0.0.1:11434/v1",
                model="qwen3.6-local:latest",
                api_key_environment="",
                organization_environment="",
                request_timeout_seconds=30,
                max_retries=0,
            ),
            request={"schema_version": 1, "prompt_version": "connectivity-v1"},
        )

        payload = json.loads(calls[0].data)
        self.assertEqual("none", payload["reasoning_effort"])
        self.assertEqual(256, payload["max_tokens"])
        self.assertEqual({"type": "json_object"}, payload["response_format"])

    def test_code_generation_sends_the_audited_messages_to_ollama_11436(self) -> None:
        calls: list[object] = []

        def opener(request: object, *, timeout: int) -> _Response:
            calls.append(request)
            return _Response(
                {
                    "choices": [
                        {
                            "message": {
                                "content": json.dumps(
                                    {
                                        "schema_version": 1,
                                        "files": [
                                            {
                                                "path": "tests/generated/test_case.py",
                                                "content": "def test_case():\n    pass\n",
                                            }
                                        ],
                                        "assumptions": [],
                                        "warnings": [],
                                    }
                                )
                            }
                        }
                    ]
                }
            )

        profile = LLMAccessProfile(
            id="ollama-code",
            version=1,
            name="Ollama code 11436",
            provider="ollama",
            base_url="http://127.0.0.1:11436/v1",
            model="qwen3.6-code:latest",
            api_key_environment="",
            organization_environment="",
            request_timeout_seconds=600,
            max_retries=0,
        )
        adapter = ConfiguredDesignLLM(environment={}, opener=opener)
        result = adapter.generate_code(
            profile=profile,
            prompt={
                "messages": [
                    {"role": "system", "content": "Cadre exact"},
                    {"role": "user", "content": "Cas exact"},
                ]
            },
        )

        self.assertEqual(1, result["schema_version"])
        self.assertEqual(
            "http://127.0.0.1:11436/v1/chat/completions",
            calls[0].full_url,
        )
        payload = json.loads(calls[0].data)
        self.assertEqual(
            [
                {"role": "system", "content": "Cadre exact"},
                {"role": "user", "content": "Cas exact"},
            ],
            payload["messages"],
        )
        self.assertEqual(0, payload["temperature"])
        self.assertEqual(32_768, payload["max_tokens"])
        self.assertEqual("none", payload["reasoning_effort"])

        with self.assertRaisesRegex(DesignLLMError, "deux messages"):
            adapter.generate_code(profile=profile, prompt={"messages": []})

    def test_missing_secret_blocks_the_call_before_network(self) -> None:
        called = False

        def opener(request: object, *, timeout: int) -> _Response:
            nonlocal called
            called = True
            return _Response({})

        adapter = ConfiguredDesignLLM(environment={}, opener=opener)
        with self.assertRaisesRegex(
            DesignLLMError,
            "DESIGN_API_KEY",
        ):
            adapter.complete(
                profile=self._profile(),
                request={"schema_version": 1},
            )
        self.assertFalse(called)

    def test_ollama_server_probe_does_not_load_the_model(self) -> None:
        urls: list[str] = []

        def opener(request: object, *, timeout: int) -> _Response:
            urls.append(request.full_url)
            if request.full_url.endswith("/api/version"):
                return _Response({"version": "0.32.3"})
            return _Response(
                {
                    "models": [
                        {
                            "name": "qwen3.6-local:latest",
                            "model": "qwen3.6-local:latest",
                        }
                    ]
                }
            )

        adapter = ConfiguredDesignLLM(environment={}, opener=opener)
        result = adapter.probe(profile=self._ollama_profile())

        self.assertEqual("Ollama", result["engine"])
        self.assertEqual("0.32.3", result["engine_version"])
        self.assertTrue(result["model_available"])
        self.assertEqual(
            [
                "http://127.0.0.1:11434/api/version",
                "http://127.0.0.1:11434/api/tags",
            ],
            urls,
        )
        self.assertNotIn("chat/completions", str(urls))

    def test_model_catalog_uses_the_provider_endpoint_and_normalizes_ids(self) -> None:
        calls: list[tuple[str, int]] = []

        def opener(request: object, *, timeout: int) -> _Response:
            calls.append((request.full_url, timeout))
            return _Response(
                {
                    "models": [
                        {"name": "qwen:latest", "model": "qwen:latest"},
                        {"name": "Gemma:latest"},
                        {"name": "qwen:latest"},
                    ]
                }
            )

        adapter = ConfiguredDesignLLM(environment={}, opener=opener)
        models = adapter.list_models(profile=self._ollama_profile())

        self.assertEqual(("Gemma:latest", "qwen:latest"), models)
        self.assertEqual(
            [("http://127.0.0.1:11434/api/tags", 30)],
            calls,
        )

    def test_openai_model_catalog_uses_the_api_key_without_exposing_it(self) -> None:
        calls: list[object] = []

        def opener(request: object, *, timeout: int) -> _Response:
            calls.append(request)
            return _Response(
                {"data": [{"id": "model-b"}, {"id": "model-a"}]}
            )

        adapter = ConfiguredDesignLLM(
            environment={"DESIGN_API_KEY": "secret-value"},
            opener=opener,
        )
        models = adapter.list_models(profile=self._profile())

        self.assertEqual(("model-a", "model-b"), models)
        self.assertEqual(
            "https://llm.example.invalid/v1/models",
            calls[0].full_url,
        )
        self.assertEqual(
            "Bearer secret-value",
            calls[0].headers["Authorization"],
        )
        self.assertNotIn("secret-value", calls[0].full_url)

    def test_anthropic_and_azure_catalogs_use_provider_specific_headers(self) -> None:
        cases = (
            (
                "anthropic",
                "https://api.anthropic.com/v1",
                "x-api-key",
                "https://api.anthropic.com/v1/models",
            ),
            (
                "azure-openai",
                "https://resource.openai.azure.com/openai/v1",
                "api-key",
                "https://resource.openai.azure.com/openai/v1/models",
            ),
        )
        for provider, base_url, header, expected_url in cases:
            with self.subTest(provider=provider):
                calls: list[object] = []

                def opener(request: object, *, timeout: int) -> _Response:
                    calls.append(request)
                    return _Response({"data": [{"id": "model-id"}]})

                adapter = ConfiguredDesignLLM(
                    environment={"PROVIDER_API_KEY": "secret-value"},
                    opener=opener,
                )
                models = adapter.list_models(
                    profile=LLMAccessProfile(
                        id=f"{provider}-catalog",
                        version=1,
                        name="Catalogue",
                        provider=provider,
                        base_url=base_url,
                        model="model-id",
                        api_key_environment="PROVIDER_API_KEY",
                        organization_environment="",
                        request_timeout_seconds=10,
                        max_retries=0,
                    )
                )

                self.assertEqual(("model-id",), models)
                self.assertEqual(expected_url, calls[0].full_url)
                normalized_headers = {
                    name.casefold(): value
                    for name, value in calls[0].headers.items()
                }
                self.assertEqual("secret-value", normalized_headers[header])
                if provider == "anthropic":
                    self.assertEqual(
                        "2023-06-01",
                        normalized_headers["anthropic-version"],
                    )

    def test_free_interaction_returns_text_and_surfaces_provider_error(self) -> None:
        calls: list[object] = []

        def successful_opener(request: object, *, timeout: int) -> _Response:
            calls.append(request)
            return _Response(
                {"choices": [{"message": {"content": "Réponse lisible"}}]}
            )

        adapter = ConfiguredDesignLLM(environment={}, opener=successful_opener)
        answer = adapter.chat(
            profile=self._ollama_profile(),
            message="Présente le modèle.",
        )

        self.assertEqual("Réponse lisible", answer)
        payload = json.loads(calls[0].data)
        self.assertNotIn("response_format", payload)
        self.assertEqual("none", payload["reasoning_effort"])

        def failing_opener(request: object, *, timeout: int) -> _Response:
            raise HTTPError(
                request.full_url,
                500,
                "Internal Server Error",
                None,
                BytesIO(
                    b'{"error":{"message":"failed to allocate CUDA_Host buffer"}}'
                ),
            )

        failing_adapter = ConfiguredDesignLLM(
            environment={},
            opener=failing_opener,
        )
        with self.assertRaisesRegex(
            DesignLLMError,
            "failed to allocate CUDA_Host buffer",
        ):
            failing_adapter.chat(
                profile=self._ollama_profile(),
                message="Bonjour",
            )

    @staticmethod
    def _profile() -> LLMAccessProfile:
        return LLMAccessProfile(
            id="design-openai",
            version=1,
            name="Conception",
            provider="openai-compatible",
            base_url="https://llm.example.invalid/v1",
            model="model",
            api_key_environment="DESIGN_API_KEY",
            organization_environment="",
            request_timeout_seconds=12,
            max_retries=0,
        )

    @staticmethod
    def _ollama_profile() -> LLMAccessProfile:
        return LLMAccessProfile(
            id="ollama-qwen",
            version=1,
            name="Ollama Qwen",
            provider="ollama",
            base_url="http://127.0.0.1:11434/v1",
            model="qwen3.6-local:latest",
            api_key_environment="",
            organization_environment="",
            request_timeout_seconds=30,
            max_retries=0,
        )


if __name__ == "__main__":
    unittest.main()
