from enum import Enum

class HnswSearchMethod(Enum):
    """HNSW (vector) search method for similarity search."""

    EUCLIDEAN = "EUCLIDEAN"
    COSINE = "COSINE"
    MANHATTAN = "MANHATTAN"
    MINKOWSKI = "MINKOWSKI"
    CHEBYSHEV = "CHEBYSHEV"
    HAMMING = "HAMMING"
