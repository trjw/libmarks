import types
from . import case, suite


class TestLoader(object):

    case_class = case.TestCase
    """The default class that all test cases should be derived from."""
    suite_class = suite.TestSuite
    """The default class that a test suite should be derived from."""
    test_method_prefix = 'test'
    """The prefix for all test methods within a test case class"""

    def get_test_case_names(self, test_case, prefix=None):
        """Return a list of all test case names within test_case"""
        if prefix is None:
            prefix = self.test_method_prefix

        def is_test_method(name):
            return self.is_test_method(name, test_case, prefix)

        names = list(filter(is_test_method, dir(test_case)))
        # TODO: Sort names
        return names

    def is_test_method(self, name, test_case, prefix=None):
        """Check whether a method is a valid test method"""
        if prefix is None:
            prefix = self.test_method_prefix
        return name.startswith(prefix) and callable(getattr(test_case, name))

    def load_tests_from_test_case(self, test_case, prefix=None):
        """Return a Test Suite with all tests contained in test_case"""
        if issubclass(test_case, self.suite_class):
            raise TypeError("Test cases should not be derived from TestSuite.")

        if prefix is None:
            prefix = self.test_method_prefix

        case_names = self.get_test_case_names(test_case, prefix)
        if not case_names and hasattr(
                test_case, test_case.default_test_method):
            case_names = [test_case.default_test_method]
        return self.suite_class(map(test_case, case_names))

    def load_tests_from_module(self, module):
        """Return a Test Suite with all tests contained in module"""
        tests = []
        for name in dir(module):
            obj = getattr(module, name)
            if isinstance(obj, type) and issubclass(obj, self.case_class):
                tests.append(self.load_tests_from_test_case(obj))

        tests = self.suite_class(tests)
        return tests

    def load_tests_from_name(self, name, module=None):
        """Return a test suite or case based on the given name"""

        path = name.split('.')
        # If no module provided, find and load the closest module
        if module is None:
            while path:
                try:
                    module = __import__('.'.join(path))
                    break
                except ImportError:
                    del path[-1]
                    if not path:
                        raise
            path = name.split('.')[1:]

        obj = module

        # Find the object containing the test
        for section in path:
            parent, obj = obj, getattr(obj, section)

        # Load the test(s) and return them
        if isinstance(obj, types.ModuleType):
            return self.load_tests_from_module(obj)
        elif isinstance(obj, type) and issubclass(obj, self.case_class):
            return self.load_tests_from_test_case(obj)
        elif (isinstance(obj, types.UnboundMethodType) and
              isinstance(parent, type) and
              issubclass(parent, self.case_class)):
            name = path[-1]
            inst = parent(name)
            return self.suite_class([inst])
        elif isinstance(obj, self.suite_class):
            return obj
        elif hasattr(obj, '__call__'):
            test = obj()
            # TODO: Should this also load tests from a test case?
            if isinstance(test, self.suite_class):
                return test
            elif isinstance(test, self.case_class):
                return self.suite_class([test])
            else:
                raise TypeError(
                    "calling {0} returned {1}, not a test".format(obj, test))
        else:
            raise TypeError("cannot make a test from: {0}".format(obj))

    def load_tests_from_names(self, names, module=None):
        """Return a test suite containing all tests in a module"""
        suites = [self.load_tests_from_name(name, module) for name in names]
        return self.suite_class(suites)


default_test_loader = TestLoader()
