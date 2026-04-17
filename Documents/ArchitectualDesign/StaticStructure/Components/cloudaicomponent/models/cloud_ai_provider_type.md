---
class: CloudAiProviderType
kind: enum
module: gafs.dynamicaiagent.cloudaicomponent.models
inherits: [AiProviderType]
---

## values

| name           | value            | description                     |
| -------------- | ---------------- | ------------------------------- |
| `AZURE_OPENAI` | `"azure-openai"` | Azure-hosted OpenAI service     |
| `OPENAI`       | `"openai"`       | Standard OpenAI API             |

## notes

- Extends `AiProviderType` (defined in `gafs.dynamicaiagent.modelcomponent.models`).
- Used as `provider_type` in `ModelDeployment` when `deployment_type == CLOUD`.
- `AiConnectionParameters` validates that `provider_type` is a `CloudAiProviderType` (or resolvable string) when `deployment_type == CLOUD`.
