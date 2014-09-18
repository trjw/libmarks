
from .case import _TestWrapper
from .result import TestResult
from .util import strclass


class TestSuite(object):

    def __init__(self, tests=()):
        self._tests = []
        self.add_tests(tests)

    def __repr__(self):
        return "<{0} tests={1}>".format(strclass(self.__class__), list(self))

    def __iter__(self):
        return iter(self._tests)

    def __call__(self, *args, **kwargs):
        return self.run(*args, **kwargs)

    def add_test(self, test):
        # sanity checks
        if not hasattr(test, '__call__'):
            raise TypeError("Test {0} is not callable".format(repr(test)))

        self._tests.append(test)

    def add_tests(self, tests):
        if isinstance(tests, basestring):
            raise TypeError("tests must be an iterable of tests, not a string")

        for test in tests:
            self.add_test(test)

    def run(self, result=None, child=False):
        original_result = result
        if result is None:
            result = TestResult()
            result.start_test_run()

        try:
            for test in self:
                self._setup_class(test, result)
                if not result.class_setup_failed(test.__class__):
                    test.run(result, child=True)

            # Tear down classes
            if not child:
                self._tear_down_classes(result)

            return result
        finally:
            result.stop_test(self)
            if original_result is None:
                # One-off test, so finish tests.
                result.stop_test_run()

    def _setup_class(self, test, result):
        class_ = test.__class__
        if result.class_setup_run(class_):
            return

        wrapper = _TestWrapper()

        # Apply options to class.
        self._apply_options(class_)

        if getattr(class_, 'setup_class', None):
            # Perform setup.
            with wrapper.test_executer(self):
                class_.setup_class()

            # TODO: Add error if setup failed.

        # Record result for all test classes. If no setup_class() method
        # available, then treat as success.
        result.add_class_setup(class_, wrapper.success)

    def _tear_down_class(self, class_, result):
        wrapper = _TestWrapper()

        if getattr(class_, 'tear_down_class', None):
            # Perform tear down.
            with wrapper.test_executer(self):
                class_.tear_down_class()

            # TODO: Add error.
            # if not wrapper.success:
            #     result.add_error()

    def _tear_down_classes(self, result):
        for class_ in result.test_classes():
            self._tear_down_class(class_, result)

    def _apply_options(self, class_):
        """Apply the appropriate options to the test class"""
        class_.__marks_options__ = getattr(self, '__marks_options__', {})
