import contextlib
import sys
import os

from .result import TestResult
from .util import strclass
from .process import Process, TimeoutProcess

BUFFER_SIZE = 8 * 1024


def marks(category, mark=None, category_marks=None):
    """Assign marks to a test or suite of tests, grouped by a category."""
    def decorator(test_item):
        if mark is None and category_marks is None:
            raise ValueError("One of mark or category_marks must be defined")
        test_item.__marks_category__ = category
        test_item.__marks_mark__ = mark
        test_item.__marks_category_marks__ = category_marks
        return test_item
    return decorator


class _TestWrapper(object):
    def __init__(self):
        self.success = True
        self.errors = []

    @contextlib.contextmanager
    def test_executer(self, test_case, is_test=False):
        old_success = self.success
        self.success = True
        try:
            yield
        except KeyboardInterrupt:
            raise
        except:
            exc_info = sys.exc_info()
            self.success = False
            self.errors.append((test_case, exc_info))
            exc_info = None
        finally:
            self.success = self.success and old_success


class TestCase(object):

    failure_exception = AssertionError
    """The exception to treat as a test failure"""
    default_test_method = 'run_test'
    """Default name for the test method"""
    process_class = Process
    """Class for a Process"""
    timeout = None
    """Timeout duration, in seconds"""

    def __init__(self, test_method_name='run_test', timeout=None):
        try:
            getattr(self, test_method_name)
        except AttributeError:
            if test_method_name != self.default_test_method:
                raise ValueError(
                    "test method %s does not exist in %s" %
                    (strclass(self.__class__), test_method_name))
        else:
            self._test_method = test_method_name

        if timeout:
            self.timeout = timeout

        # Change the process class to one that supports timeout if
        # timeout is set.
        if self.timeout and self.process_class == Process:
            self.process_class = TimeoutProcess

    def setup(self):
        pass

    def tear_down(self):
        pass

    @classmethod
    def setup_class(cls):
        pass

    @classmethod
    def tear_down_class(cls):
        pass

    def id(self):
        return "{}.{}".format(strclass(self.__class__), self._test_method)

    def __str__(self):
        return "{} ({})".format(self._test_method, strclass(self.__class__))

    def __repr__(self):
        return "<{} test_method={}>".format(
            strclass(self.__class__), self._test_method)

    def __call__(self, *args, **kwargs):
        return self.run(*args, **kwargs)

    def _process_errors(self, result, errors):
        for test_case, exc_info in errors:
            if exc_info is not None:
                if issubclass(exc_info[0], self.failure_exception):
                    result.add_failure(test_case, exc_info)
                else:
                    result.add_error(test_case, exc_info)

    @property
    def test_method(self):
        return getattr(self, self._test_method)


    def process(self, argv, input_file=None, *args, **kwargs):
        """Create a Process of the type specified for this test case"""
        # Add the timeout to the init args.
        if self.timeout:
            kwargs.setdefault('timeout', self.timeout)

        # Include the input file if it is set.
        if input_file is not None:
            kwargs['input_file'] = input_file

        # Instantiate the new process.
        p = self.process_class(argv, *args, **kwargs)

        return p

    def run(self, result=None):
        original_result = result
        if result is None:
            result = TestResult()
            result.start_test_run()

        result.start_test(self)

        wrapper = _TestWrapper()
        try:
            # Perform setup.
            with wrapper.test_executer(self):
                self.setup()

            if wrapper.success:
                # Run the test method.
                with wrapper.test_executer(self, is_test=True):
                    self.test_method()

                # Perform tear down.
                with wrapper.test_executer(self):
                    self.tear_down()

            # Process wrapper.
            self._process_errors(result, wrapper.errors)
            if wrapper.success:
                result.add_success(self)

            return result
        finally:
            result.stop_test(self)
            if original_result is None:
                # One-off test, so finish tests.
                result.stop_test_run()

    def _check_signal(self, process, msg):
        """Check if process was signalled, causing the current test to fail."""
        if process.check_signalled():
            msg = "Process received unexpected signal: {0}".format(
                process.signal)
        self._check_timeout(process, msg)

    def _check_timeout(self, process, msg):
        """Check if process was timed out, causing the test to fail."""
        if process.timeout:
            msg = "Timeout occurred"
        raise self.failure_exception(msg)

    def fail(self, msg=None):
        """Fail immediately, with the given message."""
        raise self.failure_exception(msg)

    def assert_stdout_matches_file(self, process, file_path, msg=None):
        """
        Assert that the standard output of the process matches the
        contents of the given file.
        """
        if not process.expect_stdout_file(file_path):
            msg = msg or "stdout mismatch"
            self._check_signal(process, msg)

    def assert_stderr_matches_file(self, process, file_path, msg=None):
        """
        Assert that the standard error of the process matches the
        contents of the given file.
        """
        if not process.expect_stderr_file(file_path):
            msg = msg or "stderr mismatch"
            self._check_signal(process, msg)

    def assert_stdout(self, process, output, msg=None):
        """
        Assert that the standard output of the process contains the given
        output.
        """
        if not process.expect_stdout(output):
            msg = msg or "stdout mismatch"
            self._check_signal(process, msg)

    def assert_stderr(self, process, output, msg=None):
        """
        Assert that the standard error of the process contains the given
        output.
        """
        if not process.expect_stderr(output):
            msg = msg or "stderr mismatch"
            self._check_signal(process, msg)

    def assert_exit_status(self, process, status, msg=None):
        """
        Assert that the exit status of the process matches the given status.
        """
        if not process.assert_exit_status(status):
            msg = msg or "exit status mismatch: expected {}, got {}".format(
                status, process.exit_status)
            self._check_timeout(process, msg)

    def assert_signalled(self, process, msg=None):
        """
        Assert that the process received a signal.
        """
        if not process.assert_signalled():
            msg = msg or "program did not receive signal"
            self._check_timeout(process, msg)

    def assert_signal(self, process, signal, msg=None):
        """
        Assert that the signal of the process matches the given signal.
        """
        if not process.assert_signal(signal):
            msg = msg or "signal mismatch: expected {}, got {}".format(
                signal, process.signal)
            self._check_timeout(process, msg)

    def assert_files_equal(self, file1, file2, msg=None):
        """
        Assert that the given files contain exactly the same contents.
        """
        if os.path.exists(file1) and os.path.exists(file2):
            # Files exist, so open and compare them
            f1 = open(file1, 'rb')
            f2 = open(file2, 'rb')

            different = False
            while True:
                b1 = f1.read(BUFFER_SIZE)
                b2 = f2.read(BUFFER_SIZE)

                if b1 != b2:
                    different = True
                    break

                if not b1:
                    # Reached end of file, and they are the same
                    break

            f1.close()
            f2.close()

            if not different:
                return

            msg = msg or "file mismatch: contents do not exactly match"
        else:
            msg = msg or "file missing"

        raise self.failure_exception(msg)
