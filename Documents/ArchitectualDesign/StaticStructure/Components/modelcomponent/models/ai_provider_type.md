---
class: AiProviderType
kind: enum
module: gafs.dynamicaiagent.modelcomponent.models
---

## usage

- Abstract base enum for AI provider types.
- Do **not** add provider type values directly here. Concrete provider enums (e.g. `CloudAiProviderType`) extend this class for their specific deployment family.

## known subclasses

| class                 | module                                        | deployment family |
| --------------------- | --------------------------------------------- | ----------------- |
| `CloudAiProviderType` | `gafs.dynamicaiagent.cloudaicomponent.models` | `CLOUD`           |
