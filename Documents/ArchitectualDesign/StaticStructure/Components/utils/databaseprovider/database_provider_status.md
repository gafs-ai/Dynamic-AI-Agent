---
class: DatabaseProviderStatus
kind: enum
module: gafs.dynamicaiagent.utils.databaseprovider
---

## values

| name | value | description |
|------|-------|-------------|
| `UNINITIALIZED` | `"uninitialized"` | Provider has not been initialized yet |
| `INITIALIZING` | `"initializing"` | Provider is in the process of connecting and authenticating |
| `AVAILABLE` | `"available"` | Provider is connected and ready to accept queries |
| `TEMPORARILY_UNAVAILABLE` | `"temporarily_unavailable"` | Provider is temporarily unavailable (e.g. reconnecting) |
| `ERROR` | `"error"` | Provider encountered an unrecoverable error |
| `TERMINATING` | `"terminating"` | Provider is in the process of shutting down |
| `TERMINATED` | `"terminated"` | Provider has been shut down and all resources released |
