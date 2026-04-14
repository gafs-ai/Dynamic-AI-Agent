---
class: DatabaseOperationException
kind: exception
module: gafs.dynamicaiagent.utils.databaseprovider.exceptions
inherits: [DatabaseProviderException]
---

| name | value |
|------|-------|
| `DEFAULT_MESSAGE` | `"Failed to execute Database Operation."` |

## usage

- Base class for all errors that occur during query or record operation execution.

---

## Operation Permission and Support

### UnpermittedDatabaseOperationException

```
inherits: [DatabaseOperationException]
DEFAULT_MESSAGE: "Unpermitted Database Operation."
```

Raised when the caller attempts an operation that is not permitted (e.g. due to access policy).

### UnsupportedDatabaseOperationException

```
inherits: [DatabaseOperationException]
DEFAULT_MESSAGE: "Unsupported Database Operation."
```

Raised when the caller attempts an operation not supported by this provider implementation.

---

## Query Related

### DatabaseQueryErrorException

```
inherits: [DatabaseOperationException]
DEFAULT_MESSAGE: "Database Query Error."
```

Raised when a query fails for any reason, including client-side validation failure and error responses returned by the database server.

---

## Connection Related

### DatabaseConnectionException

```
inherits: [DatabaseOperationException]
DEFAULT_MESSAGE: "Database Disconnected."
```

Raised when a query cannot be executed due to a connection problem, including: provider not connected, query timeout, and connection limit exceeded.

---

## Record Operation Related

### DatabaseRecordNotFoundException

```
inherits: [DatabaseOperationException]
DEFAULT_MESSAGE: "Database Record Not Found."
```

Raised when the requested record does not exist in the database.

### DatabaseConflictingEntryException

```
inherits: [DatabaseOperationException]
DEFAULT_MESSAGE: "Database Record Conflicts with Another Entry."
```

Raised when attempting to create a record that conflicts with another record (e.g. conflicting id, unique index violation).
