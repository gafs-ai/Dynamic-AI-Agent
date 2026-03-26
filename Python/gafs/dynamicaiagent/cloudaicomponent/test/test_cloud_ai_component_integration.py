"""
Integration tests for CloudAiComponent.

Ensures that AzureOpenAiProvider and OpenAiProvider work correctly when
invoked through CloudAiComponent. Uses the same secret config files as
the provider-specific tests.
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import pytest

# Add Python source root for imports
PYTHON_SRC = Path(__file__).resolve().parents[5]
if str(PYTHON_SRC) not in sys.path:
    sys.path.insert(0, str(PYTHON_SRC))

from gafs.dynamicaiagent.cloudaicomponent import (
    CloudAiComponent,
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
)
from gafs.dynamicaiagent.modelcomponent.models.ai_request import AiRequest
from gafs.dynamicaiagent.modelcomponent.models.ai_response import AiResponse
from gafs.dynamicaiagent.modelcomponent.models.message import Message


TEST_DIR = Path(__file__).resolve().parent


def _config_path(name: str) -> Path:
    return TEST_DIR / name


def _load_config(name: str) -> dict | None:
    p = _config_path(name)
    if not p.exists():
        return None
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def _azure_options_from_dict(d: dict, operation_type: AiOperationType) -> AiConnectionParameters:
    o = d.get("options", {})
    options = AiConnectionParameters(
        operation_type=operation_type,
        deployment_type=AiDeploymentType.CLOUD,
        provider_type=CloudAiProviderType.AZURE_OPENAI,
    )
    options.parameters = {
        "model": o.get("model", ""),
        "deployment": o.get("deployment", o.get("model", "")),
        "endpoint": o.get("endpoint", ""),
        "api_key": o.get("api_key", ""),
        "api_version": o.get("api_version", "2024-12-01-preview"),
    }
    return options


def _openai_options_from_dict(d: dict, operation_type: AiOperationType) -> AiConnectionParameters:
    o = d.get("options", {})
    options = AiConnectionParameters(
        operation_type=operation_type,
        deployment_type=AiDeploymentType.CLOUD,
        provider_type=CloudAiProviderType.OPENAI,
    )
    options.parameters = {
        "model": o.get("model", ""),
        "api_key": o.get("api_key", ""),
        "organization_id": o.get("organization_id"),
    }
    return options


def _log_response_content(test_name: str, response: AiResponse) -> None:
    """Log received content for verification."""
    logger = logging.getLogger(__name__)
    out = getattr(response, "output", None)
    if out is not None:
        if hasattr(out, "messages") and out.messages:
            content = out.messages[0].content if out.messages else ""
            logger.info("[%s] Chat content: %r", test_name, content)
        if hasattr(out, "embedding") and out.embedding:
            emb = out.embedding
            dim = len(emb) if emb else 0
            logger.info("[%s] Embedding: dimension=%d", test_name, dim)
    status = getattr(response, "status", None)
    if status is not None:
        logger.info(
            "[%s] Usage: input_tokens=%s output_tokens=%s",
            test_name,
            getattr(status, "input_tokens", None),
            getattr(status, "output_tokens", None),
        )


def _build_request(cfg: dict, operation: str) -> AiRequest:
    req_data = cfg.get("request", {})
    if operation == "chat":
        payload = ChatCompletionPayload()
        raw_messages = req_data.get("messages", [])
        messages = [
            Message.from_dict(m) if isinstance(m, dict) else m for m in raw_messages
        ]
        payload.messages = messages
        parameters = {
            "stream": req_data.get("stream", False),
            "temperature": req_data.get("temperature"),
            "max_tokens": req_data.get("max_tokens"),
            "reasoning_effort": req_data.get("reasoning_effort"),
        }
        return AiRequest(AiOperationType.CHAT_COMPLETION, payload=payload, parameters=parameters)
    if operation == "embedding":
        payload = EmbeddingPayload()
        payload.input = req_data.get("input", "")
        parameters = {"dimensions": req_data.get("dimensions")}
        return AiRequest(AiOperationType.EMBEDDING, payload=payload, parameters=parameters)
    raise ValueError(f"Unsupported operation: {operation}")


# ------------ CloudAiComponent via Azure OpenAI ------------


@pytest.mark.asyncio
async def test_cloud_ai_component_azure_chat_text():
    """CloudAiComponent delegates to AzureOpenAiProvider for chat (text)."""
    cfg = _load_config("secret_test_config_azure_openai_chat_text.json")
    if cfg is None:
        pytest.skip("secret_test_config_azure_openai_chat_text.json not found")
    component = CloudAiComponent()
    options = _azure_options_from_dict(cfg, AiOperationType.CHAT_COMPLETION)
    request = _build_request(cfg, "chat")
    request.parameters["stream"] = False
    response = await component.invoke(options, request)
    assert isinstance(response, AiResponse)
    assert response.output is not None
    assert hasattr(response.output, "messages")
    assert response.output.messages
    assert isinstance(response.output.messages[0].content, str)
    _log_response_content("cloud_azure_chat_text", response)


@pytest.mark.asyncio
async def test_cloud_ai_component_azure_chat_image():
    """CloudAiComponent delegates to AzureOpenAiProvider for chat (image)."""
    cfg = _load_config("secret_test_config_azure_openai_chat_image.json")
    if cfg is None:
        pytest.skip("secret_test_config_azure_openai_chat_image.json not found")
    component = CloudAiComponent()
    options = _azure_options_from_dict(cfg, AiOperationType.CHAT_COMPLETION)
    request = _build_request(cfg, "chat")
    response = await component.invoke(options, request)
    assert isinstance(response, AiResponse)
    assert response.output is not None
    assert response.output.messages
    assert isinstance(response.output.messages[0].content, str)
    _log_response_content("cloud_azure_chat_image", response)


@pytest.mark.asyncio
async def test_cloud_ai_component_azure_embedding():
    """CloudAiComponent delegates to AzureOpenAiProvider for embedding."""
    cfg = _load_config("secret_test_config_azure_openai_embedding.json")
    if cfg is None:
        pytest.skip("secret_test_config_azure_openai_embedding.json not found")
    component = CloudAiComponent()
    options = _azure_options_from_dict(cfg, AiOperationType.EMBEDDING)
    request = _build_request(cfg, "embedding")
    response = await component.invoke(options, request)
    assert isinstance(response, AiResponse)
    assert response.output is not None
    assert hasattr(response.output, "embedding")
    assert response.output.embedding is not None
    assert len(response.output.embedding) > 0
    _log_response_content("cloud_azure_embedding", response)


# ------------ CloudAiComponent via OpenAI ------------


@pytest.mark.asyncio
async def test_cloud_ai_component_openai_chat_text():
    """CloudAiComponent delegates to OpenAiProvider for chat (text)."""
    cfg = _load_config("secret_test_config_openai_chat_text.json")
    if cfg is None:
        pytest.skip("secret_test_config_openai_chat_text.json not found")
    component = CloudAiComponent()
    options = _openai_options_from_dict(cfg, AiOperationType.CHAT_COMPLETION)
    request = _build_request(cfg, "chat")
    request.parameters["stream"] = False
    response = await component.invoke(options, request)
    assert isinstance(response, AiResponse)
    assert response.output is not None
    assert hasattr(response.output, "messages")
    assert response.output.messages
    assert isinstance(response.output.messages[0].content, str)
    _log_response_content("cloud_openai_chat_text", response)


@pytest.mark.asyncio
async def test_cloud_ai_component_openai_chat_image():
    """CloudAiComponent delegates to OpenAiProvider for chat (image)."""
    cfg = _load_config("secret_test_config_openai_chat_image.json")
    if cfg is None:
        pytest.skip("secret_test_config_openai_chat_image.json not found")
    component = CloudAiComponent()
    options = _openai_options_from_dict(cfg, AiOperationType.CHAT_COMPLETION)
    request = _build_request(cfg, "chat")
    response = await component.invoke(options, request)
    assert isinstance(response, AiResponse)
    assert response.output is not None
    assert response.output.messages
    assert isinstance(response.output.messages[0].content, str)
    _log_response_content("cloud_openai_chat_image", response)


@pytest.mark.asyncio
async def test_cloud_ai_component_openai_embedding():
    """CloudAiComponent delegates to OpenAiProvider for embedding."""
    cfg = _load_config("secret_test_config_openai_embedding.json")
    if cfg is None:
        pytest.skip("secret_test_config_openai_embedding.json not found")
    component = CloudAiComponent()
    options = _openai_options_from_dict(cfg, AiOperationType.EMBEDDING)
    request = _build_request(cfg, "embedding")
    response = await component.invoke(options, request)
    assert isinstance(response, AiResponse)
    assert response.output is not None
    assert hasattr(response.output, "embedding")
    assert response.output.embedding is not None
    assert len(response.output.embedding) > 0
    _log_response_content("cloud_openai_embedding", response)


# ------------ Error handling ------------


@pytest.mark.asyncio
async def test_cloud_ai_component_invalid_provider_raises():
    """CloudAiComponent raises CloudAiException subclass for string provider_type."""
    options = AiConnectionParameters(
        operation_type=AiOperationType.CHAT_COMPLETION,
        deployment_type=AiDeploymentType.CLOUD,
        provider_type=CloudAiProviderType.AZURE_OPENAI,
    )
    # Override provider_type to something invalid for the match
    object.__setattr__(options, "provider_type", "unknown")
    component = CloudAiComponent()
    request = AiRequest(
        AiOperationType.CHAT_COMPLETION,
        payload=ChatCompletionPayload(),
        parameters={},
    )
    with pytest.raises(CloudAiUnsupportedOperationException) as exc_info:
        await component.invoke(options, request)
    assert isinstance(exc_info.value, CloudAiException)
    assert exc_info.value.details.get("ai_provider") == "unknown"

