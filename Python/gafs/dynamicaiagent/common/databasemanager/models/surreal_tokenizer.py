"""surreal_tokenizer.py - Enum of supported SurrealDB full-text search tokenizer types."""

from enum import Enum


class SurrealTokenizer(Enum):
    """Enum of supported SurrealDB full-text search tokenizer types.

    Each value corresponds to a SurrealDB DEFINE ANALYZER TOKENIZERS keyword.
    """

    BLANK = "blank"
    CAMEL = "camel"
    CLASS = "class"
    PUNCT = "punct"
