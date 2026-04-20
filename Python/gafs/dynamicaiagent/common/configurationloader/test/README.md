# ConfigurationLoader – Test Specification

`gafs.dynamicaiagent.common.configurationloader.test`

---

## Purpose

This test suite validates that `ConfigurationLoader.load_configurations` meets the
specification defined in the design document.  All publicly exposed methods are
covered for both normal and abnormal cases.

No mocks are used.  Folder paths are injected via the `ConfigurationLoader`
constructor's optional override parameters (`program_folder`, `app_data_folder`,
`user_home_folder`), and temporary directories are created by pytest's built-in
`tmp_path` fixture.  This means no real OS directories (home, AppData, etc.) are
touched during testing.

---

## Test files

| File | Description |
|------|-------------|
| `test_configuration_loader.py` | Tests against the Python source implementation. |
| `test_build_configuration_loader.py` | Wrapper that re-runs the same tests against the Nuitka-compiled `.pyd` module. |

---

## Normal cases (`TestLoadConfigurationsNormal`)

| Test | Description |
|------|-------------|
| `test_default_only_returns_dict` | When only the default config exists, `load_configurations(None)` returns its content as-is. |
| `test_app_data_overwrites_default_duplicate_keys` | Keys present in both default and app-data configs are taken from the app-data config; keys unique to the default are preserved. |
| `test_home_overwrites_app_data_and_default` | Home-folder config has higher priority than app-data and default; unique keys from all levels are preserved. |
| `test_custom_path_has_highest_priority` | An explicit `config_file_path` overrides all other configs for duplicate keys. |
| `test_non_duplicate_keys_all_preserved` | Keys that appear in only one config file are present in the merged result. |
| `test_app_data_absent_does_not_raise` | Missing app-data and home-folder config files are silently skipped. |
| `test_config_file_path_none_skips_custom` | Passing `None` for `config_file_path` loads only the default config. |
| `test_nested_dict_values_merged_correctly` | A key whose value is a `dict` is replaced (shallow) by the higher-priority value; no deep merge occurs. |
| `test_all_four_levels_correct_priority` | All four config levels are merged with the correct priority order (custom > home > app_data > default). |

---

## Abnormal cases (`TestLoadConfigurationsAbnormal`)

| Test | Expected exception |
|------|--------------------|
| `test_default_config_missing_raises_file_not_exist` | Default config file absent → `ConfigurationLoaderFileNotExistException` with `details["file_path"]` set. |
| `test_default_config_invalid_json_raises_invalid` | Default config contains malformed JSON → `ConfigurationLoaderInvalidConfigurationException`. |
| `test_default_config_json_array_raises_invalid` | Default config is a JSON array (not a dict) → `ConfigurationLoaderInvalidConfigurationException`. |
| `test_default_config_json_string_raises_invalid` | Default config is a JSON string (not a dict) → `ConfigurationLoaderInvalidConfigurationException`. |
| `test_app_data_config_invalid_json_raises_invalid` | App-data config contains malformed JSON → `ConfigurationLoaderInvalidConfigurationException`. |
| `test_home_config_invalid_json_raises_invalid` | Home config is a valid JSON non-dict (number) → `ConfigurationLoaderInvalidConfigurationException`. |
| `test_custom_path_missing_raises_file_not_exist` | Explicit `config_file_path` does not exist → `ConfigurationLoaderFileNotExistException`. |
| `test_custom_path_invalid_json_raises_invalid` | Explicit config path contains malformed JSON → `ConfigurationLoaderInvalidConfigurationException`. |
| `test_exception_inherits_from_configuration_loader_exception` | Both specific exceptions are sub-types of `ConfigurationLoaderException`. |
| `test_exception_details_contain_file_path` | `details["file_path"]` is always populated in raised exceptions. |

---

## Running the tests

```bash
# Source tests (from Python/ directory)
python -m pytest gafs/dynamicaiagent/common/configurationloader/test/test_configuration_loader.py -v

# Build the compiled module first, then run build tests
python gafs/dynamicaiagent/common/configurationloader/build_nuitka.py
python -m pytest gafs/dynamicaiagent/common/configurationloader/test/test_build_configuration_loader.py -v
```
