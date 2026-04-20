"""
hnsw_search_method.py - Enum of distance/similarity metrics used in HNSW vector index searches.
"""

from enum import Enum


class HnswSearchMethod(Enum):
    """Distance or similarity metric used when performing HNSW approximate nearest-neighbour searches.

    The HNSW (Hierarchical Navigable Small World) algorithm requires a metric that
    quantifies how close two vectors are.  Choosing the right metric depends on
    the nature of the embeddings and the similarity semantics required.
    """

    EUCLIDEAN = "EUCLIDEAN"
    """Euclidean (L2) distance.  Measures straight-line distance between two vectors."""

    COSINE = "COSINE"
    """Cosine similarity (default).  Measures the angle between two vectors, making
    it magnitude-invariant and well-suited for text embeddings."""

    MANHATTAN = "MANHATTAN"
    """Manhattan (L1) distance.  Sums the absolute differences along each dimension."""

    MINKOWSKI = "MINKOWSKI"
    """Minkowski distance.  Generalises L1 and L2 distances via a configurable exponent *p*."""

    CHEBYSHEV = "CHEBYSHEV"
    """Chebyshev (L∞) distance.  Equals the maximum absolute difference across all dimensions."""

    HAMMING = "HAMMING"
    """Hamming distance.  Counts the number of positions at which two vectors differ.
    Typically used with binary or integer vectors."""
