"""Azure OpenAI Provider implementing ICloudAiProvider.

Uses the official Azure OpenAI client from the openai package with
api_version and deployment support for Azure-hosted models.
Uses Model Component's AiRequest, AiResponse, AiPayload, AiOutput.
"""
from __future__ import annotations

from typing import Any, override

from openai import AsyncAzureOpenAI

from gafs.dynamicaiagent.modelcomponent.models.ai_operation_status import (
    AiOperationStatus,
    AiOperationStatusEnum,
)
from gafs.dynamicaiagent.modelcomponent.models.ai_operation_type import AiOperationType
from gafs.dynamicaiagent.modelcomponent.models.ai_output import (
    ChatCompletionOutput,
    EmbeddingOutput,
)
from gafs.dynamicaiagent.modelcomponent.models.ai_request import AiRequest
from gafs.dynamicaiagent.modelcomponent.models.ai_connection_parameters import AiConnectionParameters
from gafs.dynamicaiagent.modelcomponent.models.ai_response import AiResponse
from gafs.dynamicaiagent.modelcomponent.models.message import Message, Role

from ...exceptions import (
    CloudAiConfigurationException,
    CloudAiRemoteApiException,
    CloudAiRequestValidationException,
    CloudAiUnsupportedOperationException,
)
from ...i_cloud_ai_provider import ICloudAiProvider
from ...models.cloud_ai_provider_type import CloudAiProviderType


class AzureOpenAiProvider(ICloudAiProvider):
    """ICloudAiProvider implementation for Azure OpenAI.

    Supports chat_completion and embedding. Converts Model Component
    payloads to OpenAI API format inside the provider.
    """
    _DEFAULT_API_VERSION = "2025-06-01"
    _VALID_ROLES = frozenset({"system", "assistant", "user", "function", "tool", "developer"})

    @classmethod
    def _get_client(cls, connection_parameters: AiConnectionParameters) -> AsyncAzureOpenAI:
        endpoint = connection_parameters.parameters.get("endpoint", "").rstrip("/")
        api_key = connection_parameters.parameters.get("api_key", "")

        if endpoint == "":
            raise CloudAiConfigurationException(
                message='"endpoint" parameter is required.',
                provider=CloudAiProviderType.AZURE_OPENAI,
            )
        if api_key == "":
            raise CloudAiConfigurationException(
                message='"api_key" parameter is required.',
                provider=CloudAiProviderType.AZURE_OPENAI,
            )

        return AsyncAzureOpenAI(
            azure_endpoint=endpoint,
            azure_deployment=connection_parameters.parameters.get("deployment", ""),
            api_version=connection_parameters.parameters.get("api_version", cls._DEFAULT_API_VERSION),
            api_key=api_key,
            #azure_ad_token=connection_parameters.parameters.get("ad_token", None),
            #azure_ad_token_provider=connection_parameters.parameters.get("ad_token_provider", None),
            organization=connection_parameters.parameters.get("organization", None),
            project=connection_parameters.parameters.get("project", None),
            #webhook_secret=connection_parameters.parameters.get("webhook_secret", None),
            #websocket_base_url=connection_parameters.parameters.get("websocket_base_url", None),
            #timeout=connection_parameters.parameters.get("timeout", None),
            #max_retries=connection_parameters.parameters.get("max_retries", None),
        )

    _TEXT_CONTENT_TYPES = frozenset({"text", "output_text"})

    @classmethod
    def _extract_message_content(cls, content: Any) -> str:
        """Extract text from message content (str or list of content parts)."""
        if content is None:
            return ""
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                if item is None:
                    continue
                if isinstance(item, dict):
                    t = item.get("type")
                    if t in cls._TEXT_CONTENT_TYPES and "text" in item:
                        parts.append(str(item["text"]))
                    elif "text" in item:
                        parts.append(str(item["text"]))
                else:
                    t = getattr(item, "type", None)
                    t = t.value if hasattr(t, "value") else t
                    t = str(t) if t is not None else ""
                    if t in cls._TEXT_CONTENT_TYPES:
                        parts.append(str(getattr(item, "text", "") or ""))
                    elif hasattr(item, "text"):
                        parts.append(str(getattr(item, "text", "") or ""))
            return "".join(parts)
        return str(content) if content else ""

    @classmethod
    def _message_to_openai(cls, m: Message) -> dict[str, Any]:
        """Convert Model Component Message to OpenAI API format."""
        role = m.role.value if hasattr(m.role, "value") else str(m.role)
        if role not in cls._VALID_ROLES:
            raise CloudAiRequestValidationException(
                message=f"Invalid message role: {role!r}. Supported: {sorted(cls._VALID_ROLES)}",
                provider=CloudAiProviderType.AZURE_OPENAI,
            )
        content = m.content
        if isinstance(content, list):
            out: list[dict[str, Any]] = []
            for p in content:
                d = p.to_dict(recursive=True) if hasattr(p, "to_dict") else {}
                pt = d.get("type", "text")
                if hasattr(pt, "value"):
                    pt = pt.value
                pt = str(pt) if pt else "text"
                if pt == "text":
                    out.append({"type": "text", "text": d.get("text", "")})
                elif pt == "image_url":
                    url = d.get("url", "")
                    detail = d.get("detail", "auto")
                    out.append({"type": "image_url", "image_url": {"url": url, "detail": detail}})
                else:
                    out.append({"type": "text", "text": d.get("text", "")})
            content = out[0]["text"] if len(out) == 1 and out[0]["type"] == "text" else out
        else:
            content = content or ""
        msg: dict[str, Any] = {"role": role, "content": content}
        if m.name is not None:
            msg["name"] = m.name
        return msg

    @classmethod
    def _messages_to_openai(cls, messages: list[Message]) -> list[dict[str, Any]]:
        """Convert ChatCompletionPayload messages to OpenAI API format."""
        return [cls._message_to_openai(m) for m in (messages or [])]

    @override
    @classmethod
    async def invoke(
        cls, parameters: AiConnectionParameters, request: AiRequest
    ) -> AiResponse:

        op = request.operation_type
        op_val = op.value if hasattr(op, "value") else str(op)
        if op_val == AiOperationType.CHAT_COMPLETION.value:
            return await cls._invoke_chat(parameters, request)
        if op_val == AiOperationType.EMBEDDING.value:
            return await cls._invoke_embedding(parameters, request)
        if op_val == AiOperationType.SPEECH_TO_TEXT.value:
            raise CloudAiUnsupportedOperationException(
                message="Speech-to-text is not implemented",
                provider=CloudAiProviderType.AZURE_OPENAI,
            )
        if op_val == AiOperationType.TEXT_TO_SPEECH.value:
            raise CloudAiUnsupportedOperationException(
                message="Text-to-speech is not implemented",
                provider=CloudAiProviderType.AZURE_OPENAI,
            )
        if op_val == AiOperationType.IMAGE_GENERATION.value:
            raise CloudAiUnsupportedOperationException(
                message="Image generation is not implemented",
                provider=CloudAiProviderType.AZURE_OPENAI,
            )
        raise CloudAiUnsupportedOperationException(
            message=f"Unsupported operation: {op}",
            provider=CloudAiProviderType.AZURE_OPENAI,
        )

    @classmethod
    async def _invoke_chat(
        cls,
        connection_parameters: AiConnectionParameters,
        request: AiRequest,
    ) -> AiResponse:
        if request.payload is None:
            raise CloudAiRequestValidationException(
                message="Chat operation requires payload",
                provider=CloudAiProviderType.AZURE_OPENAI,
            )
        client = cls._get_client(connection_parameters)
        model = connection_parameters.parameters.get("deployment", "")
        messages = cls._messages_to_openai(request.payload.messages or [])
        stream = request.parameters.get("stream", False)
        kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": stream,
        }

        if request.parameters.get("temperature", None) is not None:
            kwargs["temperature"] = request.parameters.get("temperature", None)
        if request.parameters.get("max_tokens", None) is not None:
            kwargs["max_completion_tokens"] = request.parameters.get("max_tokens", None)
        if request.parameters.get("reasoning_effort", None) is not None:
            kwargs["reasoning_effort"] = request.parameters.get("reasoning_effort", None)
        try:
            resp = await client.chat.completions.create(**kwargs)
        except Exception as e:
            raise CloudAiRemoteApiException(
                message=f"Chat completion API call failed: {e}",
                cause=e,
                provider=CloudAiProviderType.AZURE_OPENAI,
            )
        usage = None
        content = ""
        if stream:
            async for chunk in resp:
                if chunk.choices:
                    delta = chunk.choices[0].delta
                    delta_content = getattr(delta, "content", None)
                    content += cls._extract_message_content(delta_content)
        else:
            if getattr(resp, "usage", None) is not None:
                u = resp.usage
                usage = AiOperationStatus()
                usage.input_tokens = getattr(u, "prompt_tokens", None) or 0
                usage.output_tokens = getattr(u, "completion_tokens", None) or 0
                usage.status = AiOperationStatusEnum.COMPLETED
            if resp.choices:
                msg = resp.choices[0].message
                raw_content = getattr(msg, "content", None)
                content = cls._extract_message_content(raw_content)
                if not content and hasattr(msg, "output") and msg.output is not None:
                    content = cls._extract_message_content(msg.output)
        out = ChatCompletionOutput()
        assistant_msg = Message()
        assistant_msg.role = Role.ASSISTANT
        assistant_msg.content = content
        out.messages = [assistant_msg]
        response = AiResponse()
        response.output = out
        if usage is not None:
            response.status = usage
        return response

    @classmethod
    async def _invoke_embedding(
        cls,
        connection_parameters: AiConnectionParameters,
        request: AiRequest,
    ) -> AiResponse:
        if request.payload is None:
            raise CloudAiRequestValidationException(
                message="Embedding operation requires payload",
                provider=CloudAiProviderType.AZURE_OPENAI,
            )
        client = cls._get_client(connection_parameters)
        model = connection_parameters.parameters.get("deployment", "")
        kwargs: dict[str, Any] = {"model": model, "input": request.payload.input}
        dims = request.parameters.get("dimensions", None)
        if dims is not None:
            kwargs["dimensions"] = dims
        try:
            resp = await client.embeddings.create(**kwargs)
        except Exception as e:
            raise CloudAiRemoteApiException(
                message=f"Embedding API call failed: {e}",
                cause=e,
                provider=CloudAiProviderType.AZURE_OPENAI,
            )
        data = [d.embedding for d in resp.data]
        emb = data[0] if data else []
        out = EmbeddingOutput()
        out.embedding = emb
        usage = None
        if getattr(resp, "usage", None) is not None:
            u = resp.usage
            usage = AiOperationStatus()
            usage.input_tokens = getattr(u, "prompt_tokens", None) or 0
            usage.output_tokens = getattr(u, "total_tokens", None) or 0
            usage.status = AiOperationStatusEnum.COMPLETED
        response = AiResponse()
        response.output = out
        if usage is not None:
            response.status = usage
        return response

