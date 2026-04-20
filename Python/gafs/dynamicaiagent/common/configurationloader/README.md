# ConfigurationLoader

`gafs.dynamicaiagent.common.configurationloader`

---

## Overview

`ConfigurationLoader` loads JSON configuration files from up to four locations and merges them into a single `dict[str, Any]`.  Higher-priority files overwrite keys that also appear in lower-priority files; unique keys from every file are preserved.

---

## Configuration file search locations (ascending priority)

| Priority | Location | Required? |
|----------|----------|-----------|
| 1 (lowest) | Program folder – the directory that contains the program files (`dynamic_ai_agent_config.json`) | **Yes** – raises `ConfigurationLoaderFileNotExistException` if absent |
| 2 | OS application-data folder (`dynamic_ai_agent_config.json`) | No – skipped if absent |
| 3 | User home folder (`dynamic_ai_agent_config.json`) | No – skipped if absent |
| 4 (highest) | Explicit path passed to `load_configurations` | No – skipped when `None`; required if not `None` |

### OS application-data folder paths

| OS | Path |
|----|------|
| Windows | `%APPDATA%\GAFS\Dynamic-AI-Agent\` |
| Linux | `~/.local/share/Dynamic-AI-Agent/` |
| macOS | `~/Library/Application Support/Dynamic-AI-Agent/` |

---

## Classes

### `IConfigurationLoader` (abstract)

Abstract base class.  Defines the public interface and the following constants:

| Constant | Value |
|----------|-------|
| `APPLICATION_NAME` | `"Dynamic-AI-Agent"` |
| `APPLICATION_AUTHOR` | `"GAFS"` |
| `CONFIGURATION_FILE_NAME` | `"dynamic_ai_agent_config.json"` |

### `ConfigurationLoader`

Concrete implementation of `IConfigurationLoader`.

#### Constructor

```python
ConfigurationLoader(
    program_folder: Path | None = None,
    app_data_folder: Path | None = None,
    user_home_folder: Path | None = None,
)
```

All three parameters are **optional** and intended for testing purposes.  In
normal production use, construct without arguments:

```python
loader = ConfigurationLoader()
config = loader.load_configurations(None)
```

When non-`None` values are supplied, they replace the automatically derived OS
folder paths, allowing unit tests to operate in isolated temporary directories
without touching real OS directories or using mock frameworks.

---

## Public Methods

### `load_configurations`

```python
def load_configurations(config_file_path: str | None) -> dict[str, Any]
```

Loads and merges all applicable configuration files.

**Parameters**

| Name | Type | Description |
|------|------|-------------|
| `config_file_path` | `str \| None` | Explicit path to an additional configuration file (e.g. supplied via `--config` on the command line).  Pass `None` if none was given. |

**Returns**

`dict[str, Any]` – merged configuration dictionary.

**Raises**

| Exception | Condition |
|-----------|-----------|
| `ConfigurationLoaderFileNotExistException` | The default configuration file does not exist, or `config_file_path` was given but the file does not exist. |
| `ConfigurationLoaderInvalidConfigurationException` | A configuration file exists but its content is not valid JSON or its top-level value is not a JSON object (`dict`). |

---

## Exceptions

All exceptions are importable from `gafs.dynamicaiagent.common.configurationloader`.

### `ConfigurationLoaderException`

Base exception for all errors from this component.  Inherits from `ApplicationException`.  `details["component"]` is always `"ConfigurationLoader"`.

### `ConfigurationLoaderFileNotExistException`

Raised when a required configuration file is missing.

`details["file_path"]` – absolute path of the missing file.

### `ConfigurationLoaderInvalidConfigurationException`

Raised when a configuration file is not a valid JSON dictionary.

`details["file_path"]` – absolute path of the invalid file.

---

## Usage example

```python
from gafs.dynamicaiagent.common.configurationloader import (
    ConfigurationLoader,
    ConfigurationLoaderFileNotExistException,
    ConfigurationLoaderInvalidConfigurationException,
)

loader = ConfigurationLoader()
try:
    config = loader.load_configurations(config_file_path=None)
except ConfigurationLoaderFileNotExistException as e:
    print("Config file not found:", e.details["file_path"])
except ConfigurationLoaderInvalidConfigurationException as e:
    print("Invalid config:", e.details["file_path"])
```
