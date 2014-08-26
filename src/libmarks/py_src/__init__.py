"""
MARKS - systems programming testing and marking framework.

Based on Python unittest framework.
"""

__all__ = [
    '__version__', 'ignore_result', 'main', 'marks', 'Process', 'TestCase',
    'TestSuite', 'TestLoader', 'default_test_loader', 'TestResult'
]

from ._version import get_version
from .process import Process
from .case import TestCase, marks, ignore_result
from .suite import TestSuite
from .loader import TestLoader, default_test_loader
from .result import TestResult
from .main import main

__version__ = get_version()
