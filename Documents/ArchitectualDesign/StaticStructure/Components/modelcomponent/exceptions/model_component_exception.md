---
class: ModelComponentException
kind: exception
module: gafs.dynamicaiagent.modelcomponent.exceptions
inherits: [ApplicationException]
---

## constants

| name | type | value |
|------|------|-------|
| `ERROR_NAME()` | `str` | `"ModelComponentException"` |
| `DEFAULT_MESSAGE()` | `str` | `"Unexpected Error in Model Component."` |

## attributes

| name | type | description |
|------|------|-------------|
| `message` | `str` | Human-readable error description. Defaults to `DEFAULT_MESSAGE`. |
| `details` | `dict[str, Any] \| None` | Optional structured details. `details["component"]` is automatically set to `"ModelComponent"` if not provided. |
| `cause` | `BaseException \| None` | Underlying exception that caused this error, if any. |

## usage

- Base exception class for all errors raised by the `ModelComponent`.
- Inherits from `ApplicationException`.

## hierarchy

```
ModelComponentException
├── ModelComponentConfigurationException
│   ├── ModelComponentInitializationException
│   ├── ModelComponentNotInitializedException
│   └── InvalidModelComponentConfigurationException
├── ModelComponentValidationException
│   ├── InvalidModelCatalogueEntryException
│   ├── InvalidModelCatalogueSearchCriteriaException
│   ├── InvalidModelDeploymentException
│   ├── InvalidModelDeploymentSearchCriteriaException
│   └── InvalidAiRequestException
├── ModelComponentConflictException
│   ├── ConflictingModelCatalogueEntryException
│   └── ConflictingModelDeploymentException
├── ModelComponentResourceNotFoundException
│   ├── ModelCatalogueEntryNotFoundException
│   └── ModelDeploymentNotFoundException
└── ModelComponentOperationException
    ├── ModelCatalogueIndexNotAvailableException
    └── FullTextAnalyzerNotExistException
```
