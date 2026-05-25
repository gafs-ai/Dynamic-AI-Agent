"""
Top-level package for the Dynamic AI Agent (`gafs`).

This file makes `gafs` a regular Python package so that subpackages
such as `gafs.dynamicaiagent` can be imported reliably.
"""

from . import dynamicaiagent

__all__ = [
    "dynamicaiagent",
]

