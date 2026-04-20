"""full_text_analyzer.py - FullTextAnalyzer data class and related definitions.

Contains:
  - FunctionDefinition: User-defined function reference.
  - TokenizerDefinition: Tokenizer type wrapper.
  - FilterDefinition: Filter type + optional parameters.
  - FullTextAnalyzer: Full analyzer definition stored in the FullTextAnalyzers collection.
"""

from __future__ import annotations

import json
from typing import Any

from surrealdb import RecordID

from .surreal_filter import SurrealFilter
from .surreal_tokenizer import SurrealTokenizer


# ---------------------------------------------------------------------------
# FunctionDefinition
# ---------------------------------------------------------------------------

class FunctionDefinition:
    """Reference to a user-defined SurrealDB function used as a tokenizer/filter.

    Attributes:
        name: Name of the user-defined function on SurrealDB.
    """

    def __init__(self) -> None:
        object.__setattr__(self, "name", None)

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "name":
            # name must be a non-empty string
            if isinstance(value, str):
                object.__setattr__(self, "name", value)
            else:
                raise ValueError(f"FunctionDefinition.name must be str, got {type(value)}")
        else:
            raise ValueError(f"Unknown attribute: {name}")

    def __repr__(self) -> str:
        return self.to_json()

    def to_dict(self, recursive: bool = False) -> dict[str, Any]:
        """Serialize to dict.

        Args:
            recursive: If True, convert all nested values to primitives.

        Returns:
            Dict representation.
        """
        result: dict[str, Any] = {}
        if self.name is not None:
            result["name"] = self.name
        return result

    def to_json(self) -> str:
        """Serialize to JSON string.

        Returns:
            JSON representation.
        """
        return json.dumps(self.to_dict(recursive=True))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FunctionDefinition":
        """Deserialize from dict.

        Args:
            data: Dict with function data.

        Returns:
            FunctionDefinition instance.
        """
        obj = cls()
        for key, value in data.items():
            if value is not None and hasattr(obj, key):
                setattr(obj, key, value)
        return obj

    @classmethod
    def from_json(cls, json_str: str) -> "FunctionDefinition":
        """Deserialize from JSON string.

        Args:
            json_str: JSON string.

        Returns:
            FunctionDefinition instance.

        Raises:
            ValueError: If json_str is not a JSON object.
        """
        converted: Any = json.loads(json_str)
        if not isinstance(converted, dict):
            raise ValueError("JSON must be an object")
        return cls.from_dict(converted)


# ---------------------------------------------------------------------------
# TokenizerDefinition
# ---------------------------------------------------------------------------

class TokenizerDefinition:
    """A single tokenizer entry in a FullTextAnalyzer definition.

    Attributes:
        tokenizer: The SurrealDB tokenizer type.
    """

    def __init__(self) -> None:
        object.__setattr__(self, "tokenizer", None)

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "tokenizer":
            if isinstance(value, SurrealTokenizer):
                object.__setattr__(self, "tokenizer", value)
            elif isinstance(value, str):
                # Auto-convert string to SurrealTokenizer enum
                object.__setattr__(self, "tokenizer", SurrealTokenizer(value))
            else:
                raise ValueError(f"TokenizerDefinition.tokenizer must be SurrealTokenizer or str, got {type(value)}")
        else:
            raise ValueError(f"Unknown attribute: {name}")

    def __repr__(self) -> str:
        return self.to_json()

    def to_dict(self, recursive: bool = False) -> dict[str, Any]:
        """Serialize to dict.

        Args:
            recursive: If True, serialize enum to its string value.

        Returns:
            Dict representation.
        """
        result: dict[str, Any] = {}
        if self.tokenizer is not None:
            result["tokenizer"] = self.tokenizer.value if recursive else self.tokenizer
        return result

    def to_json(self) -> str:
        """Serialize to JSON string.

        Returns:
            JSON representation.
        """
        return json.dumps(self.to_dict(recursive=True))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TokenizerDefinition":
        """Deserialize from dict.

        Args:
            data: Dict with tokenizer data.

        Returns:
            TokenizerDefinition instance.
        """
        obj = cls()
        for key, value in data.items():
            if value is not None and hasattr(obj, key):
                setattr(obj, key, value)
        return obj

    @classmethod
    def from_json(cls, json_str: str) -> "TokenizerDefinition":
        """Deserialize from JSON string.

        Args:
            json_str: JSON string.

        Returns:
            TokenizerDefinition instance.

        Raises:
            ValueError: If json_str is not a JSON object.
        """
        converted: Any = json.loads(json_str)
        if not isinstance(converted, dict):
            raise ValueError("JSON must be an object")
        return cls.from_dict(converted)


# ---------------------------------------------------------------------------
# FilterDefinition
# ---------------------------------------------------------------------------

class FilterDefinition:
    """A single filter entry in a FullTextAnalyzer definition.

    Attributes:
        filter: The SurrealDB filter type.
        parameters: Optional parameters (e.g. min/max for ngram, language for snowball).
    """

    @staticmethod
    def EDGENGRAM_DEFAULT_MIN() -> int:
        """Default minimum n-gram length for edgengram filter."""
        return 3

    @staticmethod
    def EDGENGRAM_DEFAULT_MAX() -> int:
        """Default maximum n-gram length for edgengram filter."""
        return 5

    @staticmethod
    def NGRAM_DEFAULT_MIN() -> int:
        """Default minimum n-gram length for ngram filter."""
        return 3

    @staticmethod
    def NGRAM_DEFAULT_MAX() -> int:
        """Default maximum n-gram length for ngram filter."""
        return 5

    @staticmethod
    def SNOWBALL_DEFAULT_LANGUAGE() -> str:
        """Default language for snowball filter."""
        return "english"

    def __init__(self) -> None:
        object.__setattr__(self, "filter", None)
        object.__setattr__(self, "parameters", None)

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "filter":
            if isinstance(value, SurrealFilter):
                object.__setattr__(self, "filter", value)
            elif isinstance(value, str):
                # Auto-convert string to SurrealFilter enum
                object.__setattr__(self, "filter", SurrealFilter(value))
            else:
                raise ValueError(f"FilterDefinition.filter must be SurrealFilter or str, got {type(value)}")
        elif name == "parameters":
            if isinstance(value, dict) or value is None:
                object.__setattr__(self, "parameters", value)
            else:
                raise ValueError(f"FilterDefinition.parameters must be dict or None, got {type(value)}")
        else:
            raise ValueError(f"Unknown attribute: {name}")

    def __repr__(self) -> str:
        return self.to_json()

    def to_dict(self, recursive: bool = False) -> dict[str, Any]:
        """Serialize to dict.

        Args:
            recursive: If True, serialize enum to its string value.

        Returns:
            Dict representation.
        """
        result: dict[str, Any] = {}
        if self.filter is not None:
            result["filter"] = self.filter.value if recursive else self.filter
        if self.parameters is not None:
            result["parameters"] = self.parameters
        return result

    def to_json(self) -> str:
        """Serialize to JSON string.

        Returns:
            JSON representation.
        """
        return json.dumps(self.to_dict(recursive=True))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FilterDefinition":
        """Deserialize from dict.

        Args:
            data: Dict with filter data.

        Returns:
            FilterDefinition instance.
        """
        obj = cls()
        for key, value in data.items():
            if value is not None and hasattr(obj, key):
                setattr(obj, key, value)
        return obj

    @classmethod
    def from_json(cls, json_str: str) -> "FilterDefinition":
        """Deserialize from JSON string.

        Args:
            json_str: JSON string.

        Returns:
            FilterDefinition instance.

        Raises:
            ValueError: If json_str is not a JSON object.
        """
        converted: Any = json.loads(json_str)
        if not isinstance(converted, dict):
            raise ValueError("JSON must be an object")
        return cls.from_dict(converted)

    def to_surreal_filter_str(self) -> str:
        """Build the SurrealQL filter string fragment for this filter.

        Returns:
            String such as "ascii", "ngram(3,5)", "snowball(english)", etc.
        """
        if self.filter is None:
            return ""

        f = self.filter
        params = self.parameters or {}

        if f == SurrealFilter.ASCII:
            return "ascii"
        elif f == SurrealFilter.LOWERCASE:
            return "lowercase"
        elif f == SurrealFilter.UPPERCASE:
            return "uppercase"
        elif f == SurrealFilter.EDGENGRAM:
            # Default min/max if not specified
            min_val = int(params.get("min", FilterDefinition.EDGENGRAM_DEFAULT_MIN()))
            max_val = int(params.get("max", FilterDefinition.EDGENGRAM_DEFAULT_MAX()))
            return f"edgengram({min_val},{max_val})"
        elif f == SurrealFilter.NGRAM:
            min_val = int(params.get("min", FilterDefinition.NGRAM_DEFAULT_MIN()))
            max_val = int(params.get("max", FilterDefinition.NGRAM_DEFAULT_MAX()))
            return f"ngram({min_val},{max_val})"
        elif f == SurrealFilter.SNOWBALL:
            lang = params.get("language", FilterDefinition.SNOWBALL_DEFAULT_LANGUAGE())
            return f"snowball({lang})"
        else:
            return f.value


# ---------------------------------------------------------------------------
# FullTextAnalyzer
# ---------------------------------------------------------------------------

class FullTextAnalyzer:
    """Full-text analyzer definition stored in the FullTextAnalyzers collection.

    This class represents a SurrealDB analyzer configuration used for full-text search.
    It encapsulates tokenizers, filters, and optional function references, and provides
    methods to generate SurrealQL statements for defining, altering, and removing the analyzer.

    Attributes:
        id: Record ID (auto-assigned by SurrealDB if not set).
        name: Unique name of the analyzer.
        function: User-defined function definitions.
        tokenizers: Tokenizer definitions.
        filters: Filter definitions.
        comment: Optional comment.
    """

    @staticmethod
    def COLLECTION_NAME() -> str:
        """Name of the SurrealDB collection for FullTextAnalyzer entries."""
        return "FullTextAnalyzers"

    @staticmethod
    def DEFAULT_ANALYZER() -> "FullTextAnalyzer":
        """Return the default n-gram analyzer definition.

        Returns:
            FullTextAnalyzer for the default_ngram_analyzer.
        """
        obj = FullTextAnalyzer()
        object.__setattr__(obj, "id", "default_ngram_analyzer")
        object.__setattr__(obj, "name", "default_ngram_analyzer")

        # Tokenizers: blank and punct
        t1 = TokenizerDefinition()
        t1.tokenizer = SurrealTokenizer.BLANK
        t2 = TokenizerDefinition()
        t2.tokenizer = SurrealTokenizer.PUNCT
        object.__setattr__(obj, "tokenizers", [t1, t2])

        # Filter: ngram(3, 5)
        f1 = FilterDefinition()
        f1.filter = SurrealFilter.NGRAM
        f1.parameters = {"min": 3, "max": 5}
        object.__setattr__(obj, "filters", [f1])

        return obj

    @staticmethod
    def DEFAULT_ENGLISH_ANALYZER() -> "FullTextAnalyzer":
        """Return the default English snowball analyzer definition.

        Returns:
            FullTextAnalyzer for the default_english_analyzer.
        """
        obj = FullTextAnalyzer()
        object.__setattr__(obj, "id", "default_english_analyzer")
        object.__setattr__(obj, "name", "default_english_analyzer")

        # Tokenizers: blank and punct
        t1 = TokenizerDefinition()
        t1.tokenizer = SurrealTokenizer.BLANK
        t2 = TokenizerDefinition()
        t2.tokenizer = SurrealTokenizer.PUNCT
        object.__setattr__(obj, "tokenizers", [t1, t2])

        # Filter: snowball(english)
        f1 = FilterDefinition()
        f1.filter = SurrealFilter.SNOWBALL
        f1.parameters = {"language": "english"}
        object.__setattr__(obj, "filters", [f1])

        return obj

    def __init__(self) -> None:
        object.__setattr__(self, "id", None)
        object.__setattr__(self, "name", None)
        object.__setattr__(self, "function", None)
        object.__setattr__(self, "tokenizers", None)
        object.__setattr__(self, "filters", None)
        object.__setattr__(self, "comment", None)

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "id":
            if value is None:
                object.__setattr__(self, "id", None)
            elif isinstance(value, str):
                object.__setattr__(self, "id", value)
            elif isinstance(value, RecordID):
                # Normalize RecordID: strip table prefix if present
                raw = str(value.id)
                object.__setattr__(self, "id", raw.split(":", 1)[-1] if ":" in raw else raw)
            else:
                raise ValueError(f"FullTextAnalyzer.id must be str or None, got {type(value)}")
        elif name == "name":
            if isinstance(value, str) or value is None:
                object.__setattr__(self, "name", value)
            else:
                raise ValueError(f"FullTextAnalyzer.name must be str or None, got {type(value)}")
        elif name == "function":
            if value is None:
                object.__setattr__(self, "function", None)
            elif isinstance(value, list):
                # Each item must be FunctionDefinition or dict (auto-convert)
                result_list = []
                for item in value:
                    if isinstance(item, FunctionDefinition):
                        result_list.append(item)
                    elif isinstance(item, dict):
                        result_list.append(FunctionDefinition.from_dict(item))
                    else:
                        raise ValueError(f"function items must be FunctionDefinition or dict")
                object.__setattr__(self, "function", result_list)
            else:
                raise ValueError(f"FullTextAnalyzer.function must be list or None")
        elif name == "tokenizers":
            if value is None:
                object.__setattr__(self, "tokenizers", None)
            elif isinstance(value, list):
                result_list = []
                for item in value:
                    if isinstance(item, TokenizerDefinition):
                        result_list.append(item)
                    elif isinstance(item, dict):
                        result_list.append(TokenizerDefinition.from_dict(item))
                    else:
                        raise ValueError(f"tokenizers items must be TokenizerDefinition or dict")
                object.__setattr__(self, "tokenizers", result_list)
            else:
                raise ValueError(f"FullTextAnalyzer.tokenizers must be list or None")
        elif name == "filters":
            if value is None:
                object.__setattr__(self, "filters", None)
            elif isinstance(value, list):
                result_list = []
                for item in value:
                    if isinstance(item, FilterDefinition):
                        result_list.append(item)
                    elif isinstance(item, dict):
                        result_list.append(FilterDefinition.from_dict(item))
                    else:
                        raise ValueError(f"filters items must be FilterDefinition or dict")
                object.__setattr__(self, "filters", result_list)
            else:
                raise ValueError(f"FullTextAnalyzer.filters must be list or None")
        elif name == "comment":
            if isinstance(value, str) or value is None:
                object.__setattr__(self, "comment", value)
            else:
                raise ValueError(f"FullTextAnalyzer.comment must be str or None, got {type(value)}")
        else:
            raise ValueError(f"Unknown attribute: {name}")

    def __repr__(self) -> str:
        return self.to_json(recursive=True)

    def to_dict(self, recursive: bool = False, exclude_id: bool = False) -> dict[str, Any]:
        """Serialize to dict.

        Args:
            recursive: If True, convert nested objects and enums to primitives.
            exclude_id: If True, exclude the id field.

        Returns:
            Dict representation.
        """
        result: dict[str, Any] = {}

        if not exclude_id and self.id is not None:
            result["id"] = self.id

        if self.name is not None:
            result["name"] = self.name

        if self.function is not None:
            result["function"] = (
                [f.to_dict(recursive=recursive) for f in self.function] if recursive
                else self.function
            )

        if self.tokenizers is not None:
            result["tokenizers"] = (
                [t.to_dict(recursive=recursive) for t in self.tokenizers] if recursive
                else self.tokenizers
            )

        if self.filters is not None:
            result["filters"] = (
                [f.to_dict(recursive=recursive) for f in self.filters] if recursive
                else self.filters
            )

        if self.comment is not None:
            result["comment"] = self.comment

        return result

    def to_json(self, recursive: bool = True, exclude_id: bool = False) -> str:
        """Serialize to JSON string.

        Args:
            recursive: If True, serialize nested objects to primitives.
            exclude_id: If True, exclude the id field.

        Returns:
            JSON representation.
        """
        return json.dumps(self.to_dict(recursive=recursive, exclude_id=exclude_id))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FullTextAnalyzer":
        """Deserialize from dict.

        Args:
            data: Dict with analyzer data.

        Returns:
            FullTextAnalyzer instance.
        """
        obj = cls()
        for key, value in data.items():
            if value is not None and hasattr(obj, key):
                setattr(obj, key, value)
        return obj

    @classmethod
    def from_json(cls, json_str: str) -> "FullTextAnalyzer":
        """Deserialize from JSON string.

        Args:
            json_str: JSON string.

        Returns:
            FullTextAnalyzer instance.

        Raises:
            ValueError: If json_str is not a JSON object.
        """
        converted: Any = json.loads(json_str)
        if not isinstance(converted, dict):
            raise ValueError("JSON must be an object")
        return cls.from_dict(converted)

    def validate_and_normalize(self) -> bool:
        """Validate and normalize the analyzer definition.

        Checks that name is non-empty and that all filter parameters are valid.

        Returns:
            True if valid.

        Raises:
            DatabaseManagerInvalidAnalyzerException: If validation fails.
        """
        # Import here to avoid circular imports at module load time
        from gafs.dynamicaiagent.common.databasemanager.exceptions import (
            DatabaseManagerInvalidAnalyzerException,
        )

        # name is required
        if not self.name:
            raise DatabaseManagerInvalidAnalyzerException(
                "FullTextAnalyzer.name is required and must not be empty."
            )

        # Validate each filter's parameters
        if self.filters:
            for fd in self.filters:
                if fd.filter is None:
                    raise DatabaseManagerInvalidAnalyzerException(
                        "FilterDefinition.filter must not be None."
                    )
                params = fd.parameters or {}
                if fd.filter in (SurrealFilter.EDGENGRAM, SurrealFilter.NGRAM):
                    min_val = params.get("min", FilterDefinition.NGRAM_DEFAULT_MIN())
                    max_val = params.get("max", FilterDefinition.NGRAM_DEFAULT_MAX())
                    if not isinstance(min_val, int) or not isinstance(max_val, int):
                        raise DatabaseManagerInvalidAnalyzerException(
                            f"Filter {fd.filter.value}: min and max must be integers."
                        )
                    if min_val < 1 or max_val < min_val:
                        raise DatabaseManagerInvalidAnalyzerException(
                            f"Filter {fd.filter.value}: min must be >= 1 and max must be >= min."
                        )
                elif fd.filter == SurrealFilter.SNOWBALL:
                    lang = params.get("language", FilterDefinition.SNOWBALL_DEFAULT_LANGUAGE())
                    if lang not in SurrealFilter.SNOWBALL_LANGUAGES():
                        raise DatabaseManagerInvalidAnalyzerException(
                            f"Filter snowball: unsupported language '{lang}'."
                        )

        # Validate each tokenizer
        if self.tokenizers:
            for td in self.tokenizers:
                if td.tokenizer is None:
                    raise DatabaseManagerInvalidAnalyzerException(
                        "TokenizerDefinition.tokenizer must not be None."
                    )

        # Validate each function
        if self.function:
            for fd in self.function:
                if not fd.name:
                    raise DatabaseManagerInvalidAnalyzerException(
                        "FunctionDefinition.name must not be empty."
                    )

        return True

    def get_define_analyzer_statement(self, overwrite: bool = False) -> str:
        """Build the DEFINE ANALYZER SurrealQL statement.

        Args:
            overwrite: If True, adds OVERWRITE; otherwise adds IF NOT EXISTS.

        Returns:
            SurrealQL DEFINE ANALYZER statement string.
        """
        keyword = "OVERWRITE" if overwrite else "IF NOT EXISTS"
        parts = [f"DEFINE ANALYZER {keyword} {self.name}"]

        # Add TOKENIZERS clause
        if self.tokenizers:
            tokenizer_strs = [t.tokenizer.value for t in self.tokenizers if t.tokenizer is not None]
            if tokenizer_strs:
                parts.append(f"TOKENIZERS {','.join(tokenizer_strs)}")

        # Add FILTERS clause
        if self.filters:
            filter_strs = [f.to_surreal_filter_str() for f in self.filters if f.filter is not None]
            if filter_strs:
                parts.append(f"FILTERS {','.join(filter_strs)}")

        # Add FUNCTION clause
        if self.function:
            fn_names = [f.name for f in self.function if f.name]
            if fn_names:
                if len(fn_names) == 1:
                    parts.append(f"FUNCTION fn::{fn_names[0]}")
                else:
                    parts.append(f"FUNCTION fn::({', '.join(fn_names)})")

        # Add COMMENT clause
        if self.comment:
            # Escape double quotes in comment
            escaped = self.comment.replace('"', '\\"')
            parts.append(f'COMMENT "{escaped}"')

        return " ".join(parts) + ";"

    def get_alter_analyzer_statement(self) -> str:
        """Build the SurrealQL statement to update (overwrite) the analyzer.

        Uses ``DEFINE ANALYZER OVERWRITE`` because ``ALTER ANALYZER`` is not supported
        in surrealdb Python client v1.0.x (embedded engine). The OVERWRITE variant
        achieves the same effect and is compatible with all supported SurrealDB versions.

        Returns:
            SurrealQL DEFINE ANALYZER OVERWRITE statement string.
        """
        # Reuse get_define_analyzer_statement with overwrite=True to produce
        # "DEFINE ANALYZER OVERWRITE <name> ..." which replaces the existing definition.
        return self.get_define_analyzer_statement(overwrite=True)

    def get_drop_analyzer_statement(self) -> str:
        """Build the REMOVE ANALYZER SurrealQL statement.

        Returns:
            SurrealQL REMOVE ANALYZER statement string.
        """
        return f"REMOVE ANALYZER {self.name};"
