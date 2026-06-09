---
class: ToolCatalogueIndexNotAvailableException
kind: exception
module: gafs.dynamicaiagent.toolcomponent.exceptions
inherits: [ToolComponentOperationException]
---

## constants

| name | type | value |
|------|------|-------|
| `ERROR_NAME()` | `str` | `"ToolCatalogueIndexNotAvailableException"` |
| `DEFAULT_MESSAGE()` | `str` | `"The tool catalogue index is currently unavailable."` |

## usage

- Raised when a vector search is attempted on `ToolCatalogue` while the HNSW index is being rebuilt.
