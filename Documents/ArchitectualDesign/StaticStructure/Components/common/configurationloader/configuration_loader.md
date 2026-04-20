---
class: ConfigurationLoader
kind: class
module: gafs.dynamicaiagent.common.configurationloader
implements:
  - IConfigurationLoader
---

## constructor

```python
def __init__(
    program_folder: Path | None = None,
    app_data_folder: Path | None = None,
    user_home_folder: Path | None = None,
) -> None
```

All parameters are optional and intended for testing purposes (folder-path injection).
In production, construct without arguments.

## methods

---

### _get_application_data_folder

```python
def _get_application_data_folder() -> Path
```

| property | value |
|----------|-------|
| description | Get the application data folder path. |

#### implementation notes

1. Get the folder path using `platformdirs.user_data_dir(APPLICATION_NAME, APPLICATION_AUTHOR, roaming=True)`.
   - Windows: `%APPDATA%\GAFS\Dynamic-AI-Agent`
   - Linux: `~/.local/share/Dynamic-AI-Agent`
   - macOS: `~/Library/Application Support/Dynamic-AI-Agent`

---

### _get_user_home_folder

```python
def _get_user_home_folder() -> Path
```

| property | value |
|----------|-------|
| description | Get the user home folder path. |

#### implementation notes

1. Get the user home directory using `Path.home()` from the Python standard library.
   (`platformdirs` does not provide a user-home API; `Path.home()` is the correct approach.)
   - Windows: `C:\Users\<username>`
   - Linux: `/home/<username>`
   - macOS: `/Users/<username>`

---

### _get_application_program_folder

```python
def _get_application_program_folder() -> Path
```

| property | value |
|----------|-------|
| description | Get the path of the folder that contains the Dynamic-AI-Agent program files. |

#### implementation notes

1. Get the folder path with `Path(__file__).parent`.

---

### load_configurations

```python
def load_configurations(config_file_path: str | None) -> dict[str, Any]
```

| property | value |
|----------|-------|
| description | Load configuration files and merge them into a single dictionary. |

#### implementation notes

1. Load the default configuration file.
   - If the file does not exist: raise `ConfigurationLoaderFileNotExistException`.
   - If the content is not a valid JSON dictionary: raise `ConfigurationLoaderInvalidConfigurationException`.
2. Load the configuration file in the application data folder if it exists, and overwrite duplicated keys.
   - If the content is not a valid JSON dictionary: raise `ConfigurationLoaderInvalidConfigurationException`.
3. Load the configuration file in the user home folder if it exists, and overwrite duplicated keys.
   - If the content is not a valid JSON dictionary: raise `ConfigurationLoaderInvalidConfigurationException`.
4. If `config_file_path` is specified, load the configuration file at that path, and overwrite duplicated keys.
   - If the file does not exist: raise `ConfigurationLoaderFileNotExistException`.
   - If the content is not a valid JSON dictionary: raise `ConfigurationLoaderInvalidConfigurationException`.
5. Return the merged configuration dictionary.

