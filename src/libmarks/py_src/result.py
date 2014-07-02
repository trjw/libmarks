from __future__ import print_function
from . import util


RESULT_TEMPLATE = "Ran {0} tests: {1} success, {2} errors, {3} failures"


class TestResult(object):
    """Container of test result information."""

    def __init__(self):
        self.failures = []
        self.errors = []
        self.successes = []
        self.tests_run = 0

    def start_test_run(self):
        """Run before the testing starts."""
        pass

    def start_test(self, test):
        """Record a test as having started."""
        self.tests_run += 1

    def stop_test(self, test):
        """Record a test as having finished."""
        pass

    def stop_test_run(self):
        """Run after all of the testing is complete."""
        pass

    def add_failure(self, test, error):
        """Record a test failure."""
        self.failures.append((test, self._exc_info_pretty_print(error, test)))

    def add_error(self, test, error):
        """Record a test error."""
        self.errors.append((test, self._exc_info_pretty_print(error, test)))

    def add_success(self, test):
        """Record a test success."""
        self.successes.append((test, None))

    def _exc_info_pretty_print(self, exc_info, test):
        exc_type, value, tb = exc_info
        return str(value)

    def __repr__(self):
        return "<{0} run={1} successes={2} errors={3} failures={4}>".format(
            util.strclass(self.__class__), self.tests_run,
            len(self.successes), len(self.errors), len(self.failures))


class PrintedTestResult(TestResult):

    def start_test_run(self):
        super(PrintedTestResult, self).start_test_run()
        print("Running tests\n")

    def start_test(self, test):
        super(PrintedTestResult, self).start_test(test)
        print("{0:60}".format(test.id()), end='')

    def stop_test(self, test):
        super(PrintedTestResult, self).stop_test(test)

    def stop_test_run(self):
        super(PrintedTestResult, self).stop_test_run()
        results = RESULT_TEMPLATE.format(
            self.tests_run, len(self.successes),
            len(self.errors), len(self.failures))
        print()
        print('-' * 70)
        print(results)

    def add_failure(self, test, error):
        super(PrintedTestResult, self).add_failure(test, error)
        print("FAIL")
        print("\t{0}".format(self._exc_info_pretty_print(error, test)))

    def add_error(self, test, error):
        super(PrintedTestResult, self).add_error(test, error)
        print("ERROR")
        print("\t{0}".format(self._exc_info_pretty_print(error, test)))

    def add_success(self, test):
        super(PrintedTestResult, self).add_success(test)
        print("OK")
