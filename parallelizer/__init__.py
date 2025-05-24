"""
Python Parallelizer - Automatic parallelization of sequential Python code.
"""

__version__ = "0.1.0"

from .analyzer import CodeAnalyzer
from .transformer import CodeTransformer
from .profiler import PerformanceProfiler

__all__ = ['CodeAnalyzer', 'CodeTransformer', 'PerformanceProfiler'] 