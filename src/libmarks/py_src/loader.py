
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
        """Return a Test Suite with all tests within test_case"""
        if issubclass(test_case, self.suite_class):
            raise TypeError("Test cases should not be derived from TestSuite.")

        if prefix is None:
            prefix = self.test_method_prefix

        case_names = self.get_test_case_names(test_case, prefix)
        if not case_names and hasattr(
                test_case, test_case.default_test_method):
            case_names = [test_case.default_test_method]
        return self.suite_class(map(test_case, case_names))


default_test_loader = TestLoader()
