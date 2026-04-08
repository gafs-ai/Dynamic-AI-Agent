---
class: ConfigurationLoaderFileNotExistException
kind: exception
module: gafs.dynamicaiagent.common.configurationloader
inherits: [ConfigurationLoaderException]
---

## constants

| name | type | value |
|------|------|-------|
| `ERROR_NAME()` | `str` | `"ConfigurationLoaderFileNotExistException"` |
| `DEFAULT_MESSAGE()` | `str` | `"Required configuration file does not exist"` |

## details schema

| key | type | description |
|-----|------|-------------|
| `"file_path"` | `str` | Path of the configuration file that was not found |

## usage

- Raised when a required configuration file does not exist or when `ConfigurationLoader` fails to read a required configuration file.
