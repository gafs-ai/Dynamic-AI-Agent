---
class: ConfigurationLoaderInvalidConfigurationException
kind: exception
module: gafs.dynamicaiagent.common.configurationloader
inherits: [ConfigurationLoaderException]
---

## constants

| name | type | value |
|------|------|-------|
| `ERROR_NAME()` | `str` | `"ConfigurationLoaderInvalidConfigurationException"` |
| `DEFAULT_MESSAGE()` | `str` | `"Invalid configuration file"` |

## details schema

| key | type | description |
|-----|------|-------------|
| `"file_path"` | `str` | Path of the configuration file with the invalid content |

## usage

- Raised when a loaded configuration file is not a valid JSON dictionary.

## notes

- `ConfigurationLoader` only validates that the file content is a valid JSON dictionary. Validation of component-specific configurations is handled by each component.
