---
class: CryptoUtilException
kind: exception
module: gafs.dynamicaiagent.utils.cryptoutil.exceptions
inherits: [Exception]
---

## attributes

| name | type | description |
|------|------|-------------|
| `message` | `str` | Human-readable error description. Defaults to `"Unexpected Error in Crypto Util."` |

## usage

- Base exception class for all errors raised by the `CryptoUtil` component.
- Does not depend on any application-level exception hierarchy; inherits directly from `Exception`.
