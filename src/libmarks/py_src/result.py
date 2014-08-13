from __future__ import division, print_function
import sys
from . import util


RESULT_TEMPLATE = "Ran {0} tests: {1} success, {2} errors, {3} failures"
RESULT_ERROR = 0
RESULT_FAILURE = 0
RESULT_SUCCESS = 1


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
        sys.stdout.flush()

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


class MarkingTestResult(TestResult):
    """Container of test result information."""

    def __init__(self):
        super(MarkingTestResult, self).__init__()
        self.marks = {}
        """Contains test case results grouped into categories."""
        self.tests_passed = 0
        self.total_tests = 0
        self.total_marks = 0
        self.received_marks = 0

    def _record_test(self, test, outcome):
        test_method = test.test_method
        # Get mark information from test method, with class fallback.
        category = (getattr(test_method, '__marks_category__', '')
                    or getattr(test.__class__, '__marks_category__', ''))
        cat_marks = (getattr(test_method, '__marks_category_marks__', 0)
                     or getattr(test.__class__, '__marks_category_marks__', 0))
        mark = (getattr(test_method, '__marks_mark__', 0)
                or getattr(test.__class__, '__marks_mark__', 0))

        r = self.marks.setdefault(category, {})

        r.setdefault('total_marks', 0)
        category_marks = r.setdefault('category_marks', cat_marks)

        if not cat_marks:
            # Individual test marks being used.
            r['total_marks'] += mark
        elif cat_marks != category_marks:
            raise ValueError(
                "Differing total marks for category '{0}' ({1} vs {2})".format(
                    category, category_marks, cat_marks))

        r.setdefault('tests', []).append(outcome)

        if r['total_marks'] and cat_marks:
            raise ValueError(
                "Category '{0}' cannot have both category marks and "
                "individual test marks".format(category))

    def stop_test_run(self):
        """Run after all of the testing is complete."""
        for category in self.marks:
            info = self.marks[category]

            # Calculate how many tests were successful.
            if info['category_marks']:
                # Overall category total marks used.
                passed = info['tests'].count(RESULT_SUCCESS)
                mark = (passed / len(info['tests'])) * info['category_marks']
                self.total_marks += info['category_marks']
            else:
                # Individual test marks used.
                failed = (
                    info['tests'].count(RESULT_FAILURE) +
                    info['tests'].count(RESULT_ERROR))
                passed = len(info['tests']) - failed
                mark = sum(info['tests'])
                self.total_marks += info['total_marks']

            info['passed'] = passed
            info['mark'] = mark
            self.tests_passed += passed
            self.total_tests += len(info['tests'])
            self.received_marks += mark

    def add_failure(self, test, error):
        """Record a test failure."""
        super(MarkingTestResult, self).add_failure(test, error)
        self._record_test(test, RESULT_FAILURE)

    def add_error(self, test, error):
        """Record a test error."""
        super(MarkingTestResult, self).add_error(test, error)
        self._record_test(test, RESULT_ERROR)

    def add_success(self, test):
        """Record a test success."""
        super(MarkingTestResult, self).add_success(test)

        test_method = test.test_method
        mark = (getattr(test_method, '__marks_mark__', 0)
                or getattr(test.__class__, '__marks_mark__', RESULT_SUCCESS))
        self._record_test(test, mark)


class UpdateTestResult(TestResult):

    def start_test_run(self):
        super(UpdateTestResult, self).start_test_run()
        print("Updating tests\n")

    def start_test(self, test):
        super(UpdateTestResult, self).start_test(test)
        if sys.stdout.isatty():
            print("\033[1m==> {0}:\033[0m".format(test.id()))
        else:
            print("==> {0}:".format(test.id()))

    def stop_test(self, test):
        print()


class DetailTestResult(TestResult):

    def start_test_run(self):
        super(DetailTestResult, self).start_test_run()
        print("Running tests - detail mode\n")

    def start_test(self, test):
        super(DetailTestResult, self).start_test(test)
        if sys.stdout.isatty():
            print("\033[1m==> {0}:\033[0m".format(test.id()))
        else:
            print("==> {0}:".format(test.id()))

    def stop_test(self, test):
        super(DetailTestResult, self).stop_test(test)
        print()

    def stop_test_run(self):
        super(DetailTestResult, self).stop_test_run()
        print("Ran {0} tests in detail mode.".format(self.tests_run))
