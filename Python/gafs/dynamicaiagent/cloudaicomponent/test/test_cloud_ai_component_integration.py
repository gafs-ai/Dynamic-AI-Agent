"""
Integration tests for CloudAiComponent.

Tests that CloudAiComponent correctly routes requests to AzureOpenAiProvider and
OpenAiProvider, and raises the right exceptions for invalid inputs.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest

from gafs.dynamicaiagent.cloudaicomponent import (
    CloudAiComponent,
    CloudAiConfigurationException,
    CloudAiException,
    CloudAiUnsupportedOperationException,
)
from gafs.dynamicaiagent.cloudaicomponent.models.cloud_ai_provider_type import CloudAiProviderType
from gafs.dynamicaiagent.modelcomponent.models.ai_connection_parameters import AiConnectionParameters
from gafs.dynamicaiagent.modelcomponent.models.ai_deployment_type import AiDeploymentType
from gafs.dynamicaiagent.modelcomponent.models.ai_operation_type import AiOperationType
from gafs.dynamicaiagent.modelcomponent.models.ai_payload import (
    ChatCompletionPayload,
    EmbeddingPayload,
    TextCompletionPayload,
)
from gafs.dynamicaiagent.modelcomponent.models.ai_request import AiRequest
from gafs.dynamicaiagent.modelcomponent.models.ai_response import AiResponse
from gafs.dynamicaiagent.modelcomponent.models.message import Message


TEST_DIR = Path(__file__).resolve().parent
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_config(name: str) -> dict | None:
    """Load a JSON config file; return None if the file does not exist."""
    path = TEST_DIR / name
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _make_azure_connection(cfg: dict, operation_type: AiOperationType) -> AiConnectionParameters:
    opts = cfg.get("options", {})
    conn = AiConnectionParameters(
        operation_type=operation_type,
        deployment_type=AiDeploymentType.CLOUD,
        provider_type=CloudAiProviderType.AZURE_OPENAI,
    )
    conn.parameters = {
        "deployment": opts.get("deployment", ""),
        "endpoint": opts.get("endpoint", ""),
        "api_key": opts.get("api_key", ""),
        "api_version": opts.get("api_version", "2024-12-01-preview"),
    }
    return conn


def _make_openai_connection(cfg: dict, operation_type: AiOperationType) -> AiConnectionParameters:
    opts = cfg.get("options", {})
    conn = AiConnectionParameters(
        operation_type=operation_type,
        deployment_type=AiDeploymentType.CLOUD,
        provider_type=CloudAiProviderType.OPENAI,
    )
    conn.parameters = {
        "model": opts.get("model", ""),
        "api_key": opts.get("api_key", ""),
        "organization_id": opts.get("organization_id"),
    }
    return conn


def _make_chat_request(cfg: dict) -> AiRequest:
    req_data = cfg.get("request", {})
    payload = ChatCompletionPayload()
    raw_messages = req_data.get("messages", [])
    messages = [Message.from_dict(m) if isinstance(m, dict) else m for m in raw_messages]
    payload.messages = messages
    parameters: dict = {"stream": req_data.get("stream", False)}
    return AiRequest(AiOperationType.CHAT_COMPLETION, payload=payload, parameters=parameters)


def _make_embedding_request(cfg: dict) -> AiRequest:
    req_data = cfg.get("request", {})
    payload = EmbeddingPayload()
    payload.text = req_data.get("text", "")
    parameters: dict = {}
    if req_data.get("dimensions") is not None:
        parameters["dimensions"] = req_data["dimensions"]
    return AiRequest(AiOperationType.EMBEDDING, payload=payload, parameters=parameters)


def _log_response(test_name: str, response: AiResponse) -> None:
    out = getattr(response, "output", None)
    if out is not None:
        if hasattr(out, "messages") and out.messages:
            logger.info("[%s] Chat content: %r", test_name, out.messages[0].content)
        if hasattr(out, "vector") and out.vector:
            logger.info("[%s] Embedding: dim=%d", test_name, len(out.vector))
    status = getattr(response, "status", None)
    if status is not None:
        logger.info(
            "[%s] Usage: input=%s output=%s",
            test_name, getattr(status, "input_tokens", None), getattr(status, "output_tokens", None),
        )


# ---------------------------------------------------------------------------
# Routing tests — Azure OpenAI
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_component_routes_to_azure_chat():
    """CloudAiComponent routes AZURE_OPENAI chat completion through to the provider."""
    cfg = _load_config("secret_test_config_azure_openai_chat_text.json")
    if cfg is None:
        pytest.skip("secret_test_config_azure_openai_chat_text.json not found")

    component = CloudAiComponent()
    conn = _make_azure_connection(cfg, AiOperationType.CHAT_COMPLETION)
    request = _make_chat_request(cfg)
    response = await component.invoke(conn, request)

    assert response.output is not None
    assert response.output.messages
    assert isinstance(response.output.messages[0].content, str)
    _log_response("component_azure_chat", response)


@pytest.mark.asyncio
async def test_component_routes_to_azure_embedding():
    """CloudAiComponent routes AZURE_OPENAI embedding through to the provider."""
    cfg = _load_config("secret_test_config_azure_openai_embedding.json")
    if cfg is None:
        pytest.skip("secret_test_config_azure_openai_embedding.json not found")

    component = CloudAiComponent()
    conn = _make_azure_connection(cfg, AiOperationType.EMBEDDING)
    request = _make_embedding_request(cfg)
    response = await component.invoke(conn, request)

    assert response.output is not None
    assert hasattr(response.output, "vector")
    assert len(response.output.vector) > 0
    _log_response("component_azure_embedding", response)


# ---------------------------------------------------------------------------
# Routing tests — OpenAI
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_component_routes_to_openai_chat():
    """CloudAiComponent routes OPENAI chat completion through to the provider."""
    cfg = _load_config("secret_test_config_openai_chat_text.json")
    if cfg is None:
        pytest.skip("secret_test_config_openai_chat_text.json not found")

    component = CloudAiComponent()
    conn = _make_openai_connection(cfg, AiOperationType.CHAT_COMPLETION)
    request = _make_chat_request(cfg)
    response = await component.invoke(conn, request)

    assert response.output is not None
    assert response.output.messages
    assert isinstance(response.output.messages[0].content, str)
    _log_response("component_openai_chat", response)


@pytest.mark.asyncio
async def test_component_routes_to_openai_embedding():
    """CloudAiComponent routes OPENAI embedding through to the provider."""
    cfg = _load_config("secret_test_config_openai_embedding.json")
    if cfg is None:
        pytest.skip("secret_test_config_openai_embedding.json not found")

    component = CloudAiComponent()
    conn = _make_openai_connection(cfg, AiOperationType.EMBEDDING)
    request = _make_embedding_request(cfg)
    response = await component.invoke(conn, request)

    assert response.output is not None
    assert hasattr(response.output, "vector")
    assert len(response.output.vector) > 0
    _log_response("component_openai_embedding", response)


# ---------------------------------------------------------------------------
# Error routing tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_component_non_cloud_deployment_raises():
    """deployment_type != CLOUD raises CloudAiConfigurationException."""
    # LOCAL deployment is not supported and raises NotImplementedError in AiConnectionParameters,
    # so we must patch the parameters directly after construction by using CLOUD first,
    # then test the component's own check by constructing parameters with a mock.
    # Since AiConnectionParameters enforces CLOUD at construction time, we simulate by
    # using a CLOUD connection and then testing a direct invocation with wrong type.
    # Instead, let's just verify the exception type is correct when the check fires.

    # We use a helper to bypass AiConnectionParameters validation: build with CLOUD,
    # then directly overwrite the internal value for the test.
    conn = AiConnectionParameters(
        operation_type=AiOperationType.CHAT_COMPLETION,
        deployment_type=AiDeploymentType.CLOUD,
        provider_type=CloudAiProviderType.AZURE_OPENAI,
    )
    # Force deployment_type to LOCAL after construction for testing the component check
    object.__setattr__(conn, "deployment_type", AiDeploymentType.LOCAL)

    payload = ChatCompletionPayload()
    msg = Message()
    msg.role = "user"
    msg.content = "Hello"
    payload.messages = [msg]
    request = AiRequest(AiOperationType.CHAT_COMPLETION, payload=payload, parameters={})

    component = CloudAiComponent()
    with pytest.raises(CloudAiConfigurationException):
        await component.invoke(conn, request)


@pytest.mark.asyncio
async def test_component_custom_string_provider_raises():
    """A custom string provider_type raises CloudAiUnsupportedOperationException."""
    conn = AiConnectionParameters(
        operation_type=AiOperationType.CHAT_COMPLETION,
        deployment_type=AiDeploymentType.CLOUD,
        provider_type="custom-unknown-provider",
    )
    conn.parameters = {"api_key": "key"}
    payload = ChatCompletionPayload()
    msg = Message()
    msg.role = "user"
    msg.content = "Hello"
    payload.messages = [msg]
    request = AiRequest(AiOperationType.CHAT_COMPLETION, payload=payload, parameters={})

    component = CloudAiComponent()
    with pytest.raises(CloudAiUnsupportedOperationException):
        await component.invoke(conn, request)
