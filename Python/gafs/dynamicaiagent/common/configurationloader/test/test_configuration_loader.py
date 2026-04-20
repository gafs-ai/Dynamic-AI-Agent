"""Tests for gafs.dynamicaiagent.common.configurationloader.

This module tests all public methods of ``ConfigurationLoader`` against the
specification defined in the design document.  Both normal and abnormal cases
are covered for ``load_configurations``.

External API connections: None (local file operations only).
Mocks: None.  Folder paths are injected via constructor overrides so that tests
operate entirely within temporary directories created by pytest's ``tmp_path``
fixture and never touch real OS directories.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from gafs.dynamicaiagent.common.configurationloader import (
    ConfigurationLoader,
    ConfigurationLoaderException,
    ConfigurationLoaderFileNotExistException,
    ConfigurationLoaderInvalidConfigurationException,
    IConfigurationLoader,
)

# Shorthand for the standard config file name.
_CFG = IConfigurationLoader.CONFIGURATION_FILE_NAME


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _write_json(folder: Path, data: object) -> Path:
    """Write *data* as JSON into ``<folder>/<_CFG>`` and return the path."""
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / _CFG
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def _write_raw(folder: Path, content: str) -> Path:
    """Write raw text content into ``<folder>/<_CFG>`` and return the path."""
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / _CFG
    path.write_text(content, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# ConfigurationLoader.load_configurations – normal cases
# ---------------------------------------------------------------------------

class TestLoadConfigurationsNormal:
    """Normal cases for ConfigurationLoader.load_configurations."""

    def test_default_only_returns_dict(self, tmp_path: Path) -> None:
        """Only the default config exists – returned dict matches its content."""
        prog = tmp_path / "prog"
        _write_json(prog, {"key1": "value1", "key2": 42})

        loader = ConfigurationLoader(program_folder=prog)
        result = loader.load_configurations(None)

        print("[TEST] default only")
        print(f"  result: {result}")

        assert result == {"key1": "value1", "key2": 42}

    def test_app_data_overwrites_default_duplicate_keys(self, tmp_path: Path) -> None:
        """App-data config overwrites keys that also appear in the default config."""
        prog = tmp_path / "prog"
        app_data = tmp_path / "appdata"
        _write_json(prog, {"key1": "default", "key2": "default"})
        _write_json(app_data, {"key1": "appdata_override"})

        loader = ConfigurationLoader(program_folder=prog, app_data_folder=app_data)
        result = loader.load_configurations(None)

        print("[TEST] app_data overwrites default")
        print(f"  result: {result}")

        # key1 comes from app-data; key2 is preserved from default.
        assert result["key1"] == "appdata_override"
        assert result["key2"] == "default"

    def test_home_overwrites_app_data_and_default(self, tmp_path: Path) -> None:
        """Home config has higher priority than app-data and default."""
        prog = tmp_path / "prog"
        app_data = tmp_path / "appdata"
        home = tmp_path / "home"
        _write_json(prog, {"key1": "default", "key2": "default"})
        _write_json(app_data, {"key1": "appdata", "key3": "appdata_only"})
        _write_json(home, {"key1": "home_override"})

        loader = ConfigurationLoader(
            program_folder=prog,
            app_data_folder=app_data,
            user_home_folder=home,
        )
        result = loader.load_configurations(None)

        print("[TEST] home overwrites app_data and default")
        print(f"  result: {result}")

        assert result["key1"] == "home_override"
        assert result["key2"] == "default"
        assert result["key3"] == "appdata_only"

    def test_custom_path_has_highest_priority(self, tmp_path: Path) -> None:
        """Explicitly specified config has highest priority over all others."""
        prog = tmp_path / "prog"
        app_data = tmp_path / "appdata"
        home = tmp_path / "home"
        custom_dir = tmp_path / "custom"
        _write_json(prog, {"key1": "default"})
        _write_json(app_data, {"key1": "appdata"})
        _write_json(home, {"key1": "home"})
        # Custom config: different file name to demonstrate explicit path.
        custom_dir.mkdir(parents=True, exist_ok=True)
        custom_path = custom_dir / "my_config.json"
        custom_path.write_text(json.dumps({"key1": "custom", "key4": "custom_only"}), encoding="utf-8")

        loader = ConfigurationLoader(
            program_folder=prog,
            app_data_folder=app_data,
            user_home_folder=home,
        )
        result = loader.load_configurations(str(custom_path))

        print("[TEST] custom path highest priority")
        print(f"  result: {result}")

        assert result["key1"] == "custom"
        assert result["key4"] == "custom_only"

    def test_non_duplicate_keys_all_preserved(self, tmp_path: Path) -> None:
        """Keys unique to each file are all present in the merged result."""
        prog = tmp_path / "prog"
        app_data = tmp_path / "appdata"
        home = tmp_path / "home"
        _write_json(prog, {"from_default": 1})
        _write_json(app_data, {"from_appdata": 2})
        _write_json(home, {"from_home": 3})

        loader = ConfigurationLoader(
            program_folder=prog,
            app_data_folder=app_data,
            user_home_folder=home,
        )
        result = loader.load_configurations(None)

        print("[TEST] non-duplicate keys all preserved")
        print(f"  result: {result}")

        assert result == {"from_default": 1, "from_appdata": 2, "from_home": 3}

    def test_app_data_absent_does_not_raise(self, tmp_path: Path) -> None:
        """No app-data or home config – load_configurations succeeds with default only."""
        prog = tmp_path / "prog"
        _write_json(prog, {"key": "value"})

        # app_data / home folders exist but contain no config file.
        loader = ConfigurationLoader(
            program_folder=prog,
            app_data_folder=tmp_path / "appdata_empty",
            user_home_folder=tmp_path / "home_empty",
        )
        result = loader.load_configurations(None)

        print("[TEST] app_data absent does not raise")
        print(f"  result: {result}")

        assert result == {"key": "value"}

    def test_config_file_path_none_skips_custom(self, tmp_path: Path) -> None:
        """Passing None for config_file_path loads only the default config."""
        prog = tmp_path / "prog"
        _write_json(prog, {"only": "default"})

        loader = ConfigurationLoader(program_folder=prog)
        result = loader.load_configurations(None)

        print("[TEST] config_file_path None skips custom")
        print(f"  result: {result}")

        assert result == {"only": "default"}

    def test_nested_dict_values_merged_correctly(self, tmp_path: Path) -> None:
        """Values that are themselves dicts replace (not deep-merge) on collision."""
        prog = tmp_path / "prog"
        app_data = tmp_path / "appdata"
        _write_json(prog, {"nested": {"a": 1, "b": 2}})
        _write_json(app_data, {"nested": {"a": 99}})

        loader = ConfigurationLoader(program_folder=prog, app_data_folder=app_data)
        result = loader.load_configurations(None)

        print("[TEST] nested dict values merged (shallow replace)")
        print(f"  result: {result}")

        # dict.update does a shallow replace of the key "nested".
        assert result["nested"] == {"a": 99}

    def test_all_four_levels_correct_priority(self, tmp_path: Path) -> None:
        """All four configuration levels are merged in the correct priority order."""
        prog = tmp_path / "prog"
        app_data = tmp_path / "appdata"
        home = tmp_path / "home"
        custom_dir = tmp_path / "custom"

        # Each level sets "shared" and a level-specific unique key.
        _write_json(prog, {"shared": "default", "default_only": "D"})
        _write_json(app_data, {"shared": "appdata", "appdata_only": "A"})
        _write_json(home, {"shared": "home", "home_only": "H"})
        custom_dir.mkdir(parents=True, exist_ok=True)
        custom_path = custom_dir / "custom.json"
        custom_path.write_text(
            json.dumps({"shared": "custom", "custom_only": "C"}),
            encoding="utf-8",
        )

        loader = ConfigurationLoader(
            program_folder=prog,
            app_data_folder=app_data,
            user_home_folder=home,
        )
        result = loader.load_configurations(str(custom_path))

        print("[TEST] all four levels priority")
        print(f"  result: {result}")

        assert result["shared"] == "custom"       # highest priority wins
        assert result["default_only"] == "D"
        assert result["appdata_only"] == "A"
        assert result["home_only"] == "H"
        assert result["custom_only"] == "C"


# ---------------------------------------------------------------------------
# ConfigurationLoader.load_configurations – abnormal cases
# ---------------------------------------------------------------------------

class TestLoadConfigurationsAbnormal:
    """Abnormal cases for ConfigurationLoader.load_configurations."""

    def test_default_config_missing_raises_file_not_exist(self, tmp_path: Path) -> None:
        """Missing default config raises ConfigurationLoaderFileNotExistException."""
        # program folder exists but contains no config file.
        prog = tmp_path / "prog"
        prog.mkdir(parents=True, exist_ok=True)

        loader = ConfigurationLoader(program_folder=prog)

        with pytest.raises(ConfigurationLoaderFileNotExistException) as exc_info:
            loader.load_configurations(None)

        exc = exc_info.value
        print("[TEST] default config missing")
        print(f"  exception: {exc}")
        print(f"  details: {exc.details}")

        assert exc.details.get("file_path") != ""
        assert isinstance(exc, ConfigurationLoaderException)

    def test_default_config_invalid_json_raises_invalid(self, tmp_path: Path) -> None:
        """Default config with malformed JSON raises ConfigurationLoaderInvalidConfigurationException."""
        prog = tmp_path / "prog"
        _write_raw(prog, "{ not valid json }")

        loader = ConfigurationLoader(program_folder=prog)

        with pytest.raises(ConfigurationLoaderInvalidConfigurationException) as exc_info:
            loader.load_configurations(None)

        exc = exc_info.value
        print("[TEST] default config invalid JSON")
        print(f"  exception: {exc}")
        print(f"  details: {exc.details}")

        assert exc.details.get("file_path") != ""

    def test_default_config_json_array_raises_invalid(self, tmp_path: Path) -> None:
        """Default config that is a JSON array (not dict) raises ConfigurationLoaderInvalidConfigurationException."""
        prog = tmp_path / "prog"
        _write_raw(prog, "[1, 2, 3]")

        loader = ConfigurationLoader(program_folder=prog)

        with pytest.raises(ConfigurationLoaderInvalidConfigurationException) as exc_info:
            loader.load_configurations(None)

        exc = exc_info.value
        print("[TEST] default config JSON array")
        print(f"  exception: {exc}")

        assert exc.details.get("file_path") != ""

    def test_default_config_json_string_raises_invalid(self, tmp_path: Path) -> None:
        """Default config that is a JSON string raises ConfigurationLoaderInvalidConfigurationException."""
        prog = tmp_path / "prog"
        _write_raw(prog, '"just a string"')

        loader = ConfigurationLoader(program_folder=prog)

        with pytest.raises(ConfigurationLoaderInvalidConfigurationException):
            loader.load_configurations(None)

    def test_app_data_config_invalid_json_raises_invalid(self, tmp_path: Path) -> None:
        """App-data config with malformed JSON raises ConfigurationLoaderInvalidConfigurationException."""
        prog = tmp_path / "prog"
        app_data = tmp_path / "appdata"
        _write_json(prog, {"key": "value"})
        _write_raw(app_data, "not json at all")

        loader = ConfigurationLoader(program_folder=prog, app_data_folder=app_data)

        with pytest.raises(ConfigurationLoaderInvalidConfigurationException) as exc_info:
            loader.load_configurations(None)

        exc = exc_info.value
        print("[TEST] app_data config invalid JSON")
        print(f"  details: {exc.details}")

        assert exc.details.get("file_path") != ""

    def test_home_config_invalid_json_raises_invalid(self, tmp_path: Path) -> None:
        """Home config with malformed JSON raises ConfigurationLoaderInvalidConfigurationException."""
        prog = tmp_path / "prog"
        home = tmp_path / "home"
        _write_json(prog, {"key": "value"})
        _write_raw(home, "123")  # valid JSON but not a dict

        loader = ConfigurationLoader(program_folder=prog, user_home_folder=home)

        with pytest.raises(ConfigurationLoaderInvalidConfigurationException) as exc_info:
            loader.load_configurations(None)

        exc = exc_info.value
        print("[TEST] home config not a dict (valid JSON)")
        print(f"  details: {exc.details}")

        assert exc.details.get("file_path") != ""

    def test_custom_path_missing_raises_file_not_exist(self, tmp_path: Path) -> None:
        """Explicit config path that does not exist raises ConfigurationLoaderFileNotExistException."""
        prog = tmp_path / "prog"
        _write_json(prog, {"key": "value"})
        missing_path = str(tmp_path / "nonexistent" / "config.json")

        loader = ConfigurationLoader(program_folder=prog)

        with pytest.raises(ConfigurationLoaderFileNotExistException) as exc_info:
            loader.load_configurations(missing_path)

        exc = exc_info.value
        print("[TEST] custom path missing")
        print(f"  details: {exc.details}")

        assert exc.details.get("file_path") != ""

    def test_custom_path_invalid_json_raises_invalid(self, tmp_path: Path) -> None:
        """Explicit config path with malformed JSON raises ConfigurationLoaderInvalidConfigurationException."""
        prog = tmp_path / "prog"
        _write_json(prog, {"key": "value"})
        custom_dir = tmp_path / "custom"
        custom_dir.mkdir(parents=True, exist_ok=True)
        bad_cfg = custom_dir / "bad.json"
        bad_cfg.write_text("{bad json", encoding="utf-8")

        loader = ConfigurationLoader(program_folder=prog)

        with pytest.raises(ConfigurationLoaderInvalidConfigurationException):
            loader.load_configurations(str(bad_cfg))

    def test_exception_inherits_from_configuration_loader_exception(
        self, tmp_path: Path
    ) -> None:
        """Both specific exceptions are sub-types of ConfigurationLoaderException."""
        prog = tmp_path / "prog"
        prog.mkdir(parents=True, exist_ok=True)

        loader = ConfigurationLoader(program_folder=prog)

        with pytest.raises(ConfigurationLoaderException):
            # Missing default config – raises ConfigurationLoaderFileNotExistException,
            # which is-a ConfigurationLoaderException.
            loader.load_configurations(None)

    def test_exception_details_contain_file_path(self, tmp_path: Path) -> None:
        """Exception details always contain the 'file_path' key."""
        prog = tmp_path / "prog"
        _write_raw(prog, "null")  # valid JSON but not a dict

        loader = ConfigurationLoader(program_folder=prog)

        with pytest.raises(ConfigurationLoaderInvalidConfigurationException) as exc_info:
            loader.load_configurations(None)

        assert "file_path" in exc_info.value.details
