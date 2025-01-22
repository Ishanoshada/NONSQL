"""
NONSQL - A unique database implementation with time-based partitioning
and Bloom filter optimization
"""

from .database import Database,DatabaseConfig

__version__ = "1.1.1"
__all__ = ["Database","DatabaseConfig"]