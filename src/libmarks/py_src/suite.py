
from .case import _TestWrapper
from .result import TestResult
from .util import strclass


class TestSuite(object):

    def __init__(self, tests=()):
        self._tests = []

        # Classes
        self._test_class_setup = []
        self._test_class_failed_setup = []

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
            raise TypeError("Test {} is not callable".format(repr(test)))

        self._tests.append(test)

    def add_tests(self, tests):
        if isinstance(tests, basestring):
            raise TypeError("tests must be an iterable of tests, not a string")

        for test in tests:
            self.add_test(test)

    def run(self, result=None):
        original_result = result
        if result is None:
            result = TestResult()
            result.start_test_run()

        try:
            for test in self:
                self._setup_class(test, result)
                if test.__class__ not in self._test_class_failed_setup:
                    test.run(result)

            # Tear down classes
            self._tear_down_classes(result)

            return result
        finally:
            result.stop_test(self)
            if original_result is None:
                # One-off test, so finish tests.
                result.stop_test_run()

    def _setup_class(self, test, result):
        class_ = test.__class__
        if class_ in self._test_class_setup:
            return

        wrapper = _TestWrapper()

        # Perform setup.
        with wrapper.test_executer(self, result):
            class_.setup_class()

        # TODO: Add error.
        # if wrapper.success:
        #     self._test_class_setup.append(class_)
        # else:
        #     self._test_class_failed_setup.append(class_)

    def _tear_down_class(self, class_, result):
        wrapper = _TestWrapper()

        # Perform setup.
        with wrapper.test_executer(self, result):
            class_.tear_down_class()

        # TODO: Add error.
        # if not wrapper.success:
        #     result.add_error()

    def _tear_down_classes(self, result):
        for class_ in self._test_class_setup:
            self._tear_down_class(class_, result)
