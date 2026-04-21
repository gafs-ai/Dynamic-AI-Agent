"""
Integration tests for OpenAiProvider.

Tests real API calls against the standard OpenAI API using config files in this directory.
Each test loads its credentials from a secret_test_config_openai_*.json file
and skips if the file is absent.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest

from gafs.dynamicaiagent.cloudaicomponent import (
    CloudAiUnsupportedOperationException,
    OpenAiProvider,
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


def _make_openai_connection(cfg: dict, operation_type: AiOperationType) -> AiConnectionParameters:
    """Build AiConnectionParameters for OpenAI from a config dict."""
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
    """Build an AiRequest for chat completion from a config dict."""
    req_data = cfg.get("request", {})
    payload = ChatCompletionPayload()
    raw_messages = req_data.get("messages", [])
    messages = [Message.from_dict(m) if isinstance(m, dict) else m for m in raw_messages]
    payload.messages = messages
    parameters: dict = {
        "stream": req_data.get("stream", False),
    }
    if req_data.get("temperature") is not None:
        parameters["temperature"] = req_data["temperature"]
    if req_data.get("max_tokens") is not None:
        parameters["max_tokens"] = req_data["max_tokens"]
    if req_data.get("reasoning_effort") is not None:
        parameters["reasoning_effort"] = req_data["reasoning_effort"]
    return AiRequest(AiOperationType.CHAT_COMPLETION, payload=payload, parameters=parameters)


def _make_embedding_request(cfg: dict) -> AiRequest:
    """Build an AiRequest for embedding from a config dict."""
    req_data = cfg.get("request", {})
    payload = EmbeddingPayload()
    payload.text = req_data.get("text", "")
    parameters: dict = {}
    if req_data.get("dimensions") is not None:
        parameters["dimensions"] = req_data["dimensions"]
    return AiRequest(AiOperationType.EMBEDDING, payload=payload, parameters=parameters)


def _log_response(test_name: str, response) -> None:
    """Log response content for manual verification."""
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
# Normal cases (happy path)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_openai_provider_chat_text():
    """Chat completion with plain text message succeeds and returns non-empty content."""
    cfg = _load_config("secret_test_config_openai_chat_text.json")
    if cfg is None:
        pytest.skip("secret_test_config_openai_chat_text.json not found")

    conn = _make_openai_connection(cfg, AiOperationType.CHAT_COMPLETION)
    request = _make_chat_request(cfg)
    response = await OpenAiProvider.invoke(conn, request)

    assert response.output is not None
    assert response.output.messages
    assert isinstance(response.output.messages[0].content, str)
    assert len(response.output.messages[0].content) > 0
    _log_response("openai_chat_text", response)


@pytest.mark.asyncio
async def test_openai_provider_chat_image():
    """Chat completion with an image URL message succeeds and returns a description."""
    cfg = _load_config("secret_test_config_openai_chat_image.json")
    if cfg is None:
        pytest.skip("secret_test_config_openai_chat_image.json not found")

    conn = _make_openai_connection(cfg, AiOperationType.CHAT_COMPLETION)
    request = _make_chat_request(cfg)
    response = await OpenAiProvider.invoke(conn, request)

    assert response.output is not None
    assert response.output.messages
    assert isinstance(response.output.messages[0].content, str)
    assert len(response.output.messages[0].content) > 0
    _log_response("openai_chat_image", response)


@pytest.mark.asyncio
async def test_openai_provider_embedding():
    """Embedding request succeeds and returns a non-empty vector."""
    cfg = _load_config("secret_test_config_openai_embedding.json")
    if cfg is None:
        pytest.skip("secret_test_config_openai_embedding.json not found")

    conn = _make_openai_connection(cfg, AiOperationType.EMBEDDING)
    request = _make_embedding_request(cfg)
    response = await OpenAiProvider.invoke(conn, request)

    assert response.output is not None
    assert hasattr(response.output, "vector")
    assert response.output.vector is not None
    assert len(response.output.vector) > 0
    _log_response("openai_embedding", response)


@pytest.mark.asyncio
async def test_openai_provider_chat_text_streaming():
    """Streaming chat completion accumulates content from chunks."""
    cfg = _load_config("secret_test_config_openai_chat_text.json")
    if cfg is None:
        pytest.skip("secret_test_config_openai_chat_text.json not found")

    conn = _make_openai_connection(cfg, AiOperationType.CHAT_COMPLETION)
    request = _make_chat_request(cfg)
    request.parameters["stream"] = True
    response = await OpenAiProvider.invoke(conn, request)

    assert response.output is not None
    assert response.output.messages
    assert isinstance(response.output.messages[0].content, str)
    _log_response("openai_chat_text_stream", response)


# ---------------------------------------------------------------------------
# Error cases (unsupported operations)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_openai_provider_text_to_speech_raises():
    """TEXT_TO_SPEECH raises CloudAiUnsupportedOperationException."""
    conn = AiConnectionParameters(
        operation_type=AiOperationType.TEXT_TO_SPEECH,
        deployment_type=AiDeploymentType.CLOUD,
        provider_type=CloudAiProviderType.OPENAI,
    )
    conn.parameters = {"model": "tts-1", "api_key": "dummy-key"}
    payload = TextCompletionPayload()
    payload.text = "hello"
    request = AiRequest(AiOperationType.TEXT_TO_SPEECH, payload=payload, parameters={})

    with pytest.raises(CloudAiUnsupportedOperationException):
        await OpenAiProvider.invoke(conn, request)


@pytest.mark.asyncio
async def test_openai_provider_image_generation_raises():
    """IMAGE_GENERATION raises CloudAiUnsupportedOperationException."""
    conn = AiConnectionParameters(
        operation_type=AiOperationType.IMAGE_GENERATION,
        deployment_type=AiDeploymentType.CLOUD,
        provider_type=CloudAiProviderType.OPENAI,
    )
    conn.parameters = {"model": "dall-e-3", "api_key": "dummy-key"}
    payload = TextCompletionPayload()
    payload.text = "a cat"
    request = AiRequest(AiOperationType.IMAGE_GENERATION, payload=payload, parameters={})

    with pytest.raises(CloudAiUnsupportedOperationException):
        await OpenAiProvider.invoke(conn, request)


@pytest.mark.asyncio
async def test_openai_provider_speech_to_text_raises():
    """SPEECH_TO_TEXT raises CloudAiUnsupportedOperationException."""
    conn = AiConnectionParameters(
        operation_type=AiOperationType.SPEECH_TO_TEXT,
        deployment_type=AiDeploymentType.CLOUD,
        provider_type=CloudAiProviderType.OPENAI,
    )
    conn.parameters = {"model": "whisper-1", "api_key": "dummy-key"}
    payload = TextCompletionPayload()
    payload.text = ""
    request = AiRequest(AiOperationType.SPEECH_TO_TEXT, payload=payload, parameters={})

    with pytest.raises(CloudAiUnsupportedOperationException):
        await OpenAiProvider.invoke(conn, request)


@pytest.mark.asyncio
async def test_openai_provider_missing_api_key_raises():
    """Missing api_key raises CloudAiConfigurationException."""
    from gafs.dynamicaiagent.cloudaicomponent import CloudAiConfigurationException

    conn = AiConnectionParameters(
        operation_type=AiOperationType.CHAT_COMPLETION,
        deployment_type=AiDeploymentType.CLOUD,
        provider_type=CloudAiProviderType.OPENAI,
    )
    conn.parameters = {"model": "gpt-4o"}
    payload = ChatCompletionPayload()
    msg = Message()
    msg.role = "user"
    msg.content = "Hello"
    payload.messages = [msg]
    request = AiRequest(AiOperationType.CHAT_COMPLETION, payload=payload, parameters={})

    with pytest.raises(CloudAiConfigurationException):
        await OpenAiProvider.invoke(conn, request)


@pytest.mark.asyncio
async def test_openai_provider_missing_model_raises():
    """Missing model raises CloudAiConfigurationException."""
    from gafs.dynamicaiagent.cloudaicomponent import CloudAiConfigurationException

    conn = AiConnectionParameters(
        operation_type=AiOperationType.CHAT_COMPLETION,
        deployment_type=AiDeploymentType.CLOUD,
        provider_type=CloudAiProviderType.OPENAI,
    )
    conn.parameters = {"api_key": "dummy-key"}
    payload = ChatCompletionPayload()
    msg = Message()
    msg.role = "user"
    msg.content = "Hello"
    payload.messages = [msg]
    request = AiRequest(AiOperationType.CHAT_COMPLETION, payload=payload, parameters={})

    with pytest.raises(CloudAiConfigurationException):
        await OpenAiProvider.invoke(conn, request)


@pytest.mark.asyncio
async def test_openai_provider_null_payload_raises():
    """None payload raises CloudAiRequestValidationException."""
    from gafs.dynamicaiagent.cloudaicomponent import CloudAiRequestValidationException

    conn = AiConnectionParameters(
        operation_type=AiOperationType.CHAT_COMPLETION,
        deployment_type=AiDeploymentType.CLOUD,
        provider_type=CloudAiProviderType.OPENAI,
    )
    conn.parameters = {"model": "gpt-4o", "api_key": "dummy-key"}
    request = AiRequest(AiOperationType.CHAT_COMPLETION)

    with pytest.raises(CloudAiRequestValidationException):
        await OpenAiProvider.invoke(conn, request)
