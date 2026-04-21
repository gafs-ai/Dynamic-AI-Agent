"""AzureOpenAiProvider — ICloudAiProvider implementation for Azure OpenAI."""

from __future__ import annotations

from typing import Any

from openai import AsyncAzureOpenAI

from gafs.dynamicaiagent.modelcomponent.models.ai_connection_parameters import AiConnectionParameters
from gafs.dynamicaiagent.modelcomponent.models.ai_operation_status import (
    AiOperationStatus,
    AiOperationStatusEnum,
)
from gafs.dynamicaiagent.modelcomponent.models.ai_operation_type import AiOperationType
from gafs.dynamicaiagent.modelcomponent.models.ai_output import ChatCompletionOutput, EmbeddingOutput
from gafs.dynamicaiagent.modelcomponent.models.ai_request import AiRequest
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

    Supports CHAT_COMPLETION and EMBEDDING operations.
    All methods are classmethods; no instance state is maintained.
    """

    _DEFAULT_API_VERSION = "2025-06-01"

    # Valid roles accepted by the OpenAI / Azure OpenAI chat API
    _VALID_ROLES = frozenset({"system", "assistant", "user", "function", "tool", "developer"})

    # Content type strings that carry text
    _TEXT_CONTENT_TYPES = frozenset({"text", "output_text"})

    @classmethod
    def _get_client(cls, connection_parameters: AiConnectionParameters) -> AsyncAzureOpenAI:
        """Build and return an AsyncAzureOpenAI client from connection_parameters.

        Raises:
            CloudAiConfigurationException: If endpoint or api_key is missing.
        """
        endpoint = connection_parameters.parameters.get("endpoint", "").rstrip("/")
        api_key = connection_parameters.parameters.get("api_key", "")

        if not endpoint:
            raise CloudAiConfigurationException(
                message='"endpoint" parameter is required.',
                provider=CloudAiProviderType.AZURE_OPENAI,
            )
        if not api_key:
            raise CloudAiConfigurationException(
                message='"api_key" parameter is required.',
                provider=CloudAiProviderType.AZURE_OPENAI,
            )

        return AsyncAzureOpenAI(
            azure_endpoint=endpoint,
            azure_deployment=connection_parameters.parameters.get("deployment", ""),
            api_version=connection_parameters.parameters.get("api_version", cls._DEFAULT_API_VERSION),
            api_key=api_key,
            organization=connection_parameters.parameters.get("organization", None),
            project=connection_parameters.parameters.get("project", None),
        )

    @classmethod
    def _extract_message_content(cls, content: Any) -> str:
        """Extract plain text from a message content value (str or list of content parts)."""
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
                    t_str = str(t) if t is not None else ""
                    if t_str in cls._TEXT_CONTENT_TYPES:
                        parts.append(str(getattr(item, "text", "") or ""))
                    elif hasattr(item, "text"):
                        parts.append(str(getattr(item, "text", "") or ""))
            return "".join(parts)
        return str(content)

    @classmethod
    def _message_to_openai(cls, m: Message) -> dict[str, Any]:
        """Convert a Message to the OpenAI API dict format.

        Raises:
            CloudAiRequestValidationException: If the message role is not accepted by the API.
        """
        role = m.role.value if hasattr(m.role, "value") else str(m.role)
        if role not in cls._VALID_ROLES:
            raise CloudAiRequestValidationException(
                message=f"Invalid message role: {role!r}. Supported: {sorted(cls._VALID_ROLES)}",
                provider=CloudAiProviderType.AZURE_OPENAI,
            )

        content = m.content
        if isinstance(content, list):
            # Convert list[MessagePart] to list[dict] for the API
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
            # If there is only a single text part, unwrap it to a plain string
            content_value: Any = (
                out[0]["text"] if len(out) == 1 and out[0]["type"] == "text" else out
            )
        else:
            content_value = content or ""

        msg: dict[str, Any] = {"role": role, "content": content_value}
        if m.name is not None:
            msg["name"] = m.name
        return msg

    @classmethod
    def _messages_to_openai(cls, messages: list[Message]) -> list[dict[str, Any]]:
        """Convert a list of Messages to the OpenAI API format."""
        return [cls._message_to_openai(m) for m in (messages or [])]

    @classmethod
    async def invoke(
        cls,
        connection_parameters: AiConnectionParameters,
        request: AiRequest,
    ) -> AiResponse:
        """Route the request to the appropriate private method based on operation_type.

        Raises:
            CloudAiUnsupportedOperationException: For unsupported operation types.
        """
        op = request.operation_type
        op_val = op.value if hasattr(op, "value") else str(op)

        if op_val == AiOperationType.CHAT_COMPLETION.value:
            return await cls._invoke_chat(connection_parameters, request)
        if op_val == AiOperationType.EMBEDDING.value:
            return await cls._invoke_embedding(connection_parameters, request)
        if op_val == AiOperationType.SPEECH_TO_TEXT.value:
            raise CloudAiUnsupportedOperationException(
                message="Speech-to-text is not implemented by AzureOpenAiProvider.",
                provider=CloudAiProviderType.AZURE_OPENAI,
            )
        if op_val == AiOperationType.TEXT_TO_SPEECH.value:
            raise CloudAiUnsupportedOperationException(
                message="Text-to-speech is not implemented by AzureOpenAiProvider.",
                provider=CloudAiProviderType.AZURE_OPENAI,
            )
        if op_val == AiOperationType.IMAGE_GENERATION.value:
            raise CloudAiUnsupportedOperationException(
                message="Image generation is not implemented by AzureOpenAiProvider.",
                provider=CloudAiProviderType.AZURE_OPENAI,
            )
        raise CloudAiUnsupportedOperationException(
            message=f"Unsupported operation type: {op}",
            provider=CloudAiProviderType.AZURE_OPENAI,
        )

    @classmethod
    async def _invoke_chat(
        cls,
        connection_parameters: AiConnectionParameters,
        request: AiRequest,
    ) -> AiResponse:
        """Execute a chat completion request against Azure OpenAI."""
        if request.payload is None:
            raise CloudAiRequestValidationException(
                message="Chat completion requires a non-None payload.",
                provider=CloudAiProviderType.AZURE_OPENAI,
            )

        client = cls._get_client(connection_parameters)
        model = connection_parameters.parameters.get("deployment", "")
        messages = cls._messages_to_openai(request.payload.messages or [])
        stream = request.parameters.get("stream", False)

        # Build keyword args for the API call
        kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": stream,
        }
        if request.parameters.get("temperature") is not None:
            kwargs["temperature"] = request.parameters["temperature"]
        if request.parameters.get("max_tokens") is not None:
            kwargs["max_completion_tokens"] = request.parameters["max_tokens"]
        if request.parameters.get("reasoning_effort") is not None:
            kwargs["reasoning_effort"] = request.parameters["reasoning_effort"]

        try:
            resp = await client.chat.completions.create(**kwargs)
        except Exception as e:
            raise CloudAiRemoteApiException(
                message=f"Chat completion API call failed: {e}",
                cause=e,
                provider=CloudAiProviderType.AZURE_OPENAI,
            )

        # Extract content and usage from the response
        content = ""
        usage: AiOperationStatus | None = None

        if stream:
            # Accumulate streaming chunks
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
                raw_content = getattr(resp.choices[0].message, "content", None)
                content = cls._extract_message_content(raw_content)

        # Build the response
        assistant_msg = Message()
        assistant_msg.role = Role.ASSISTANT
        assistant_msg.content = content

        out = ChatCompletionOutput()
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
        """Execute an embedding request against Azure OpenAI."""
        if request.payload is None:
            raise CloudAiRequestValidationException(
                message="Embedding requires a non-None payload.",
                provider=CloudAiProviderType.AZURE_OPENAI,
            )

        client = cls._get_client(connection_parameters)
        model = connection_parameters.parameters.get("deployment", "")

        kwargs: dict[str, Any] = {
            "model": model,
            "input": request.payload.text,
        }
        if request.parameters.get("dimensions") is not None:
            kwargs["dimensions"] = request.parameters["dimensions"]

        try:
            resp = await client.embeddings.create(**kwargs)
        except Exception as e:
            raise CloudAiRemoteApiException(
                message=f"Embedding API call failed: {e}",
                cause=e,
                provider=CloudAiProviderType.AZURE_OPENAI,
            )

        # Extract embedding vector from the first result
        embedding_vector = resp.data[0].embedding if resp.data else []

        usage: AiOperationStatus | None = None
        if getattr(resp, "usage", None) is not None:
            u = resp.usage
            usage = AiOperationStatus()
            usage.input_tokens = getattr(u, "prompt_tokens", None) or 0
            usage.output_tokens = getattr(u, "total_tokens", None) or 0
            usage.status = AiOperationStatusEnum.COMPLETED

        out = EmbeddingOutput()
        out.vector = embedding_vector

        response = AiResponse()
        response.output = out
        if usage is not None:
            response.status = usage
        return response
