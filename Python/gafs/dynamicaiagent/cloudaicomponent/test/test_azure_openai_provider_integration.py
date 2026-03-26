"""
Integration tests for AzureOpenAiProvider.

Runs against secret_test_config_azure_openai_*.json config files.
Skips tests when config files are not present.
Uses Model Component's AiRequest and AiResponse.
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
    AzureOpenAiProvider,
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


def _options_from_dict(d: dict, operation_type: AiOperationType) -> AiConnectionParameters:
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


def _log_response_content(test_name: str, response) -> None:
    """Log received content for verification."""
    logger = logging.getLogger(__name__)
    out = getattr(response, "output", None)
    if out is not None:
        if hasattr(out, "messages") and out.messages:
            content = out.messages[0].content if out.messages else ""
            logger.info("[%s] Chat content: %r", test_name, content)
        if hasattr(out, "embedding") and out.embedding:
            emb = out.embedding
            n = 1
            dim = len(emb) if emb else 0
            logger.info("[%s] Embedding: %d vectors, dimension=%d", test_name, n, dim)
    status = getattr(response, "status", None)
    if status is not None:
        logger.info("[%s] Usage: input_tokens=%s output_tokens=%s", test_name, getattr(status, "input_tokens", None), getattr(status, "output_tokens", None))


def _build_request(cfg: dict, operation: str) -> AiRequest:
    req_data = cfg.get("request", {})
    if operation == "chat":
        payload = ChatCompletionPayload()
        raw_messages = req_data.get("messages", [])
        messages = [Message.from_dict(m) if isinstance(m, dict) else m for m in raw_messages]
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


@pytest.mark.asyncio
async def test_azure_openai_provider_chat_text():
    cfg = _load_config("secret_test_config_azure_openai_chat_text.json")
    if cfg is None:
        pytest.skip("secret_test_config_azure_openai_chat_text.json not found")
    options = _options_from_dict(cfg, AiOperationType.CHAT_COMPLETION)
    request = _build_request(cfg, "chat")
    request.parameters["stream"] = False
    response = await AzureOpenAiProvider.invoke(options, request)
    assert response.output is not None
    assert hasattr(response.output, "messages")
    assert response.output.messages
    assert isinstance(response.output.messages[0].content, str)
    _log_response_content("azure_chat_text", response)


@pytest.mark.asyncio
async def test_azure_openai_provider_chat_image():
    cfg = _load_config("secret_test_config_azure_openai_chat_image.json")
    if cfg is None:
        pytest.skip("secret_test_config_azure_openai_chat_image.json not found")
    options = _options_from_dict(cfg, AiOperationType.CHAT_COMPLETION)
    request = _build_request(cfg, "chat")
    response = await AzureOpenAiProvider.invoke(options, request)
    assert response.output is not None
    assert response.output.messages
    assert isinstance(response.output.messages[0].content, str)
    _log_response_content("azure_chat_image", response)


@pytest.mark.asyncio
async def test_azure_openai_provider_embedding():
    cfg = _load_config("secret_test_config_azure_openai_embedding.json")
    if cfg is None:
        pytest.skip("secret_test_config_azure_openai_embedding.json not found")
    options = _options_from_dict(cfg, AiOperationType.EMBEDDING)
    request = _build_request(cfg, "embedding")
    response = await AzureOpenAiProvider.invoke(options, request)
    assert response.output is not None
    assert hasattr(response.output, "embedding")
    assert response.output.embedding is not None
    assert len(response.output.embedding) > 0
    assert len(response.output.embedding) == 1024 or len(response.output.embedding) > 0
    _log_response_content("azure_embedding", response)


@pytest.mark.asyncio
async def test_azure_openai_provider_speech_to_text():
    pytest.skip("Speech-to-text requires provider-specific payload conversion (not yet implemented)")


@pytest.mark.asyncio
async def test_azure_openai_provider_text_to_speech_not_implemented():
    options = AiConnectionParameters(
        operation_type=AiOperationType.TEXT_TO_SPEECH,
        deployment_type=AiDeploymentType.CLOUD,
        provider_type=CloudAiProviderType.AZURE_OPENAI,
    )
    options.parameters = {
        "model": "tts-model",
        "deployment": "tts-model",
        "endpoint": "https://test.openai.azure.com/",
        "api_key": "key",
        "api_version": "2024-12-01-preview",
    }
    from gafs.dynamicaiagent.modelcomponent.models.ai_payload import TextCompletionPayload
    payload = TextCompletionPayload()
    payload.text = "hello"
    request = AiRequest(AiOperationType.TEXT_TO_SPEECH, payload=payload, parameters={})
    with pytest.raises(CloudAiUnsupportedOperationException):
        await AzureOpenAiProvider.invoke(options, request)


@pytest.mark.asyncio
async def test_azure_openai_provider_image_generation_not_implemented():
    options = AiConnectionParameters(
        operation_type=AiOperationType.IMAGE_GENERATION,
        deployment_type=AiDeploymentType.CLOUD,
        provider_type=CloudAiProviderType.AZURE_OPENAI,
    )
    options.parameters = {
        "model": "dall-e",
        "deployment": "dall-e",
        "endpoint": "https://test.openai.azure.com/",
        "api_key": "key",
        "api_version": "2024-12-01-preview",
    }
    from gafs.dynamicaiagent.modelcomponent.models.ai_payload import TextCompletionPayload
    payload = TextCompletionPayload()
    payload.text = "a cat"
    request = AiRequest(AiOperationType.IMAGE_GENERATION, payload=payload, parameters={})
    with pytest.raises(CloudAiUnsupportedOperationException):
        await AzureOpenAiProvider.invoke(options, request)
