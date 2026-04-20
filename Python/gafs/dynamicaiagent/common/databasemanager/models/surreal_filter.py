"""surreal_filter.py - Enum of supported SurrealDB full-text search filter types."""

from enum import Enum


class SurrealFilter(Enum):
    """Enum of supported SurrealDB full-text search filter types.

    Each value corresponds to a SurrealDB DEFINE ANALYZER FILTERS keyword.

    NOTE: 'mapper' filters are not supported.
    """

    ASCII = "ascii"
    LOWERCASE = "lowercase"
    UPPERCASE = "uppercase"
    EDGENGRAM = "edgengram"
    NGRAM = "ngram"
    SNOWBALL = "snowball"

    @staticmethod
    def SNOWBALL_LANGUAGES() -> list[str]:
        """Return the list of languages supported by the snowball filter.

        Returns:
            List of valid snowball language strings.
        """
        return [
            "arabic", "danish", "dutch", "english", "french", "german", "greek",
            "hungarian", "italian", "norwegian", "portuguese", "romanian", "russian",
            "spanish", "swedish", "tamil", "turkish",
        ]
