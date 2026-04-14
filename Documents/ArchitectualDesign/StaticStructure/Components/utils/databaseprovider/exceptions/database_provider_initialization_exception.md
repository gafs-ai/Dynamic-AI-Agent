---
class: DatabaseProviderInitializationException
kind: exception
module: gafs.dynamicaiagent.utils.databaseprovider.exceptions
inherits: [DatabaseProviderException]
---

| name | value |
|------|-------|
| `DEFAULT_MESSAGE` | `"Failed to initialize Database Provider."` |

## usage

- Raised when a provider fails to initialize (connect, authenticate, or apply options).

---

## DatabaseProviderOptionsException

```
inherits: [DatabaseProviderInitializationException]
DEFAULT_MESSAGE: "Invalid Database Provider Options."
```

Raised when the provided `DatabaseProviderOptions` are invalid or incomplete.

---

## DatabaseProviderUnconnectableException

```
inherits: [DatabaseProviderInitializationException]
DEFAULT_MESSAGE: "Database Provider is not connectable."
```

Raised when the provider cannot establish a network connection to the database endpoint.

---

## DatabaseProviderAuthenticationException

```
inherits: [DatabaseProviderInitializationException]
DEFAULT_MESSAGE: "Database Provider Authentication Failed."
```

Raised when credentials are rejected during provider initialization.

---

## EmbeddedDatabaseInitializationException

```
inherits: [DatabaseProviderInitializationException]
DEFAULT_MESSAGE: "Failed to initialize Embedded Database."
```

Raised when an embedded database provider fails during startup, covering all failure cases including server process startup failure, port conflicts, and insufficient resources.
