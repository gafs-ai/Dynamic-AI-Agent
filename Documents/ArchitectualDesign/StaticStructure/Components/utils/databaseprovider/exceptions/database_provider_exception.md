---
class: DatabaseProviderException
kind: exception
module: gafs.dynamicaiagent.utils.databaseprovider.exceptions
inherits: [Exception]
---

## attributes

| name | type | description |
|------|------|-------------|
| `message` | `str` | Human-readable error description. Defaults to `"Unexpected Error in Database Provider."` |
| `details` | `dict[str, Any] \| None` | Optional structured details. |
| `cause` | `BaseException \| None` | Underlying exception that caused this error, if any. |

## usage

- Base exception class for all errors raised by the `DatabaseProvider` component.
- Does not depend on any application-level exception hierarchy; inherits directly from `Exception`.

## hierarchy

```
DatabaseProviderException
├── DatabaseProviderInitializationException
│   ├── DatabaseProviderOptionsException
│   ├── DatabaseProviderUnconnectableException
│   ├── DatabaseProviderAuthenticationException
│   └── EmbeddedDatabaseInitializationException
└── DatabaseOperationException
    ├── UnpermittedDatabaseOperationException
    ├── UnsupportedDatabaseOperationException
    ├── DatabaseQueryErrorException
    ├── DatabaseConnectionException
    ├── DatabaseRecordNotFoundException
    └── DatabaseConflictingEntryException
```
