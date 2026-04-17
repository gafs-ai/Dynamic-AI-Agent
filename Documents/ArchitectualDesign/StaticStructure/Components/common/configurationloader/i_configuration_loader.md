---
class: IConfigurationLoader
kind: abstract_class
module: gafs.dynamicaiagent.common.configurationloader
inherits: [ABC]
exceptions_used:
  - ConfigurationLoaderFileNotExistException
  - ConfigurationLoaderInvalidConfigurationException
---

## constants

| name | type | value |
|------|------|-------|
| `APPLICATION_NAME()` | `str` | `"Dynamic-AI-Agent"` |
| `APPLICATION_AUTHOR()` | `str` | `"GAFS"` |
| `CONFIGURATION_FILE_NAME()` | `str` | `"dynamic_ai_agent_config.json"` |

## methods

---

### load_configurations

```python
def load_configurations(config_file_path: str | None) -> dict[str, Any]
```

| property | value |
|----------|-------|
| description | Load configuration files and merge them into a single dictionary. |

#### parameters

| name | type | required | description |
|------|------|----------|-------------|
| `config_file_path` | `str \| None` | no | Path of a configuration file specified as a launch option. `None` if not specified. |

#### returns

| type | description |
|------|-------------|
| `dict[str, Any]` | Merged configuration dictionary. |

#### raises

| exception | condition |
|-----------|-----------|
| `ConfigurationLoaderFileNotExistException` | A required configuration file does not exist. |
| `ConfigurationLoaderInvalidConfigurationException` | A configuration file is not a valid JSON dictionary. |

#### rules

- If multiple configuration files exist, duplicated keys are overwritten in ascending priority order:
  1. Default configuration file
  2. Configuration file in the application data folder
  3. Configuration file in the user home folder
  4. Configuration file specified as a launch option (`--config "{config_file_path}"`)
- Only duplicated keys are overwritten; non-duplicated keys from all files are preserved.

