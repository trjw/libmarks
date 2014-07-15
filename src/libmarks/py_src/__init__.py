"""
MARKS - systems programming testing and marking framework.

Based on Python unittest framework.
"""

__all__ = [
    'main', 'marks', 'Process', 'TestCase', 'TestSuite', 'TestLoader',
    'default_test_loader', 'TestResult'
]

from .process import Process
from .case import TestCase, marks
from .suite import TestSuite
from .loader import TestLoader, default_test_loader
from .result import TestResult
from .main import main
