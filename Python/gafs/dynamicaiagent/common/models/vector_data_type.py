"""
vector_data_type.py - Enum of numeric data types used to store vector components.
"""

from enum import Enum


class VectorDataType(Enum):
    """Numeric data type used to store each component of a vector embedding.

    Choosing a narrower type (e.g. ``F32`` instead of ``F64``) reduces storage
    and memory requirements at the cost of precision.  Select the type that
    matches the precision of your embedding model's output.
    """

    F64 = "F64"
    """64-bit (double-precision) floating-point.  Highest precision; largest memory footprint."""

    F32 = "F32"
    """32-bit (single-precision) floating-point (default).  Balances precision and efficiency.
    Most embedding models output float32 vectors."""

    I64 = "I64"
    """64-bit signed integer.  Suitable for integer-valued embeddings."""

    I32 = "I32"
    """32-bit signed integer."""

    I16 = "I16"
    """16-bit signed integer.  Smallest integer type; maximum compression at the
    cost of range and precision."""
