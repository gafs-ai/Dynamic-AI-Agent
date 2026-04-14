---
class: RetryOptions
kind: data_class
roles: [value_object]
module: gafs.dynamicaiagent.utils.databaseprovider
---

## attributes

| name | type | required | default | description |
|------|------|----------|---------|-------------|
| `timeout` | `int` | no | `60` | Request timeout in seconds. A connection attempt that exceeds this duration is treated as a timeout error. |
| `max_retry` | `int` | no | `2` | Maximum number of retry attempts on connection errors. `0` = no retry. |
| `retry_interval` | `int` | no | `10` | Base retry interval in seconds. The actual wait before retry `n` (1-based) is `retry_interval × n`, growing linearly with each attempt. |

## retry interval schedule

For `retry_interval = 10` and `max_retry = 3`:

| retry | wait before attempt |
|-------|---------------------|
| 1st | 10 s |
| 2nd | 20 s |
| 3rd | 30 s |

## notes

- `RetryOptions` applies only to **connection errors** (timeout, endpoint unreachable). It does not apply to authentication errors (`DatabaseProviderAuthenticationException`) or query errors (`DatabaseQueryErrorException`).
- An instance can be supplied per-request via `query` / `query_raw`, overriding the provider-level default set in `DatabaseProviderOptions.retry_options`.
- If neither a per-request nor a provider-level `RetryOptions` is present, the default values above are used.
