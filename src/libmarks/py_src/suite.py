
import sys
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
                self._setup_module(test, result)
                self._setup_class(test, result)
                module_name = test.__class__.__module__
                if not (result.module_setup_failed(module_name) or
                        result.class_setup_failed(test.__class__)):
                    test.run(result, child=True)

            # Tear down classes
            if not child:
                self._tear_down_classes(result)
                self._tear_down_modules(result)

            return result
        finally:
            if original_result is None:
                # One-off test, so finish tests.
                result.stop_test_run()

    def _setup_module(self, test, result):
        module_name = test.__class__.__module__
        if module_name == __name__:
            # Do not attempt to setup this module.
            return
        elif result.module_setup_run(module_name):
            # Module setup has already been run.
            return

        try:
            module = sys.modules[module_name]
        except KeyError:
            return

        wrapper = _TestWrapper()

        if getattr(module, 'setup_module', None):
            with wrapper.test_executer(self):
                options = getattr(self, '__marks_options__', {})
                module.setup_module(options)

        # Record result for module setup. If no setup_module() method
        # available, then treat as success.
        result.add_module_setup(module_name, wrapper.success)

    def _tear_down_module(self, module_name, result):
        try:
            module = sys.modules[module_name]
        except KeyError:
            return

        wrapper = _TestWrapper()

        if getattr(module, 'tear_down_module', None):
            # Perform tear down.
            with wrapper.test_executer(self):
                options = getattr(self, '__marks_options__', {})
                module.tear_down_module(options)

            # TODO: Add error.
            # if not wrapper.success:
            #     result.add_error()

    def _tear_down_modules(self, result):
        for module_name in result.test_modules():
            self._tear_down_module(module_name, result)

    def _setup_class(self, test, result):
        class_ = test.__class__

        # Apply options to class.
        self._apply_options(class_)

        if result.class_setup_run(class_):
            # Class setup has already been run.
            return
        elif result.module_setup_failed(class_.__module__):
            # Do not setup class if the module failed setup.
            return

        wrapper = _TestWrapper()

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
