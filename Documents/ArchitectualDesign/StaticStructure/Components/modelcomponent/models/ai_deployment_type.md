---
class: AiDeploymentType
kind: enum
module: gafs.dynamicaiagent.modelcomponent.models
---

## values

| name | value | description |
|------|-------|-------------|
| `CLOUD` | `"cloud"` | Hosted AI service accessed via API (e.g. Azure OpenAI) |
| `LOCAL` | `"local"` | Model running locally within the application process |
| `REMOTE` | `"remote"` | Model running on a separate self-hosted server |
