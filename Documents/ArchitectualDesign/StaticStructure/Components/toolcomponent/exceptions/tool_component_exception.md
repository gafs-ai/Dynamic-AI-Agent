---
class: ToolComponentException
kind: exception
module: gafs.dynamicaiagent.toolcomponent.exceptions
inherits: [ApplicationException]
---

## constants

| name | type | value |
|------|------|-------|
| `ERROR_NAME()` | `str` | `"ToolComponentException"` |
| `DEFAULT_MESSAGE()` | `str` | `"Unexpected Error in Tool Component."` |

## attributes

| name | type | description |
|------|------|-------------|
| `message` | `str` | Human-readable error description. Defaults to `DEFAULT_MESSAGE`. |
| `details` | `dict[str, Any] \| None` | Optional structured details. `details["component"]` is automatically set to `"ToolComponent"` if not provided. |
| `cause` | `BaseException \| None` | Underlying exception that caused this error, if any. |

## usage

- Base exception class for all errors raised by the `ToolComponent`.
- Inherits from `ApplicationException`.

## hierarchy

```
ToolComponentException
├── ToolComponentConfigurationException
│   ├── ToolComponentInitializationException
│   ├── ToolComponentNotInitializedException
│   └── InvalidToolComponentConfigurationException
├── ToolComponentValidationException
│   ├── InvalidToolCatalogueEntryException
│   ├── InvalidToolCatalogueSearchCriteriaException
│   ├── InvalidToolVersionEntryException
│   ├── InvalidToolVersionSearchCriteriaException
│   ├── InvalidSandboxCatalogueEntryException
│   ├── InvalidSandboxCatalogueSearchCriteriaException
│   └── InvalidToolInvocationException
├── ToolComponentConflictException
│   ├── ConflictingToolCatalogueEntryException
│   ├── ConflictingToolVersionEntryException
│   └── ConflictingSandboxCatalogueEntryException
├── ToolComponentResourceNotFoundException
│   ├── ToolCatalogueEntryNotFoundException
│   ├── ToolVersionEntryNotFoundException
│   └── SandboxCatalogueEntryNotFoundException
└── ToolComponentOperationException
    ├── ToolCatalogueIndexNotAvailableException
    └── FullTextAnalyzerNotExistException
```
