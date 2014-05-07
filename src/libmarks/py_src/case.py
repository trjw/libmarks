import contextlib
import sys

from .result import TestResult
from .util import strclass


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

    def __init__(self, test_method_name='run_test'):
        try:
            getattr(self, test_method_name)
        except AttributeError:
            if test_method_name != 'run_test':
                raise ValueError(
                    "test method %s does not exist in %s" %
                    (strclass(self.__class__), test_method_name))
        else:
            self._test_method = test_method_name

    def setup(self):
        pass

    def tear_down(self):
        pass

    @classmethod
    def setup_class(self):
        pass

    @classmethod
    def tear_down_class(self):
        pass

    def id(self):
        return "%s.%s" % (strclass(self.__class__), self._test_method)

    def __str__(self):
        return "%s (%s)" % (self._test_method, strclass(self.__class__))

    def __repr__(self):
        return "<%s test_method=%s>" % (
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

    def run(self, result=None):
        original_result = result
        if result is None:
            result = TestResult()
            result.start_test_run()

        result.start_test(self)

        test_method = getattr(self, self._test_method)

        wrapper = _TestWrapper()
        try:
            # Perform setup.
            with wrapper.test_executer(self, result):
                self.setup()

            if wrapper.success:
                # Run the test method.
                with wrapper.test_executer(self, result):
                    test_method()

                # Perform tear down.
                with wrapper.test_executer(self, result):
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
            raise self.failure_exception(msg)

    def assert_stderr_matches_file(self, process, file_path, msg=None):
        """
        Assert that the standard error of the process matches the
        contents of the given file.
        """
        if not process.expect_stdout_file(file_path):
            msg = msg or "stderr mismatch"
            raise self.failure_exception(msg)

    def assert_stdout(self, process, output, msg=None):
        """
        Assert that the standard output of the process contains the given
        output.
        """
        if not process.expect_stdout(output):
            msg = msg or "stdout mismatch"
            raise self.failure_exception(msg)

    def assert_stderr(self, process, output, msg=None):
        """
        Assert that the standard error of the process contains the given
        output.
        """
        if not process.expect_stderr(output):
            msg = msg or "stderr mismatch"
            raise self.failure_exception(msg)

    def assert_exit_status(self, process, status, msg=None):
        """
        Assert that the exit status of the process matches the given status.
        """
        if not process.assert_exit_status(status):
            msg = msg or "exit status mismatch: expected %d, got %d" % (
                status, process.exit_status)
            raise self.failure_exception(msg)

    def assert_signalled(self, process, msg=None):
        """
        Assert that the process received a signal.
        """
        if not process.assert_signalled():
            msg = msg or "program did not receive signal"
            raise self.failure_exception(msg)

    def assert_signal(self, process, signal, msg=None):
        """
        Assert that the signal of the process matches the given signal.
        """
        if not process.assert_signal(signal):
            msg = msg or "signal mismatch: expected %d, got %d" % (
                signal, process.signal)
            raise self.failure_exception(msg)
