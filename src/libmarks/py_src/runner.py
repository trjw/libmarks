from __future__ import division, print_function
import os
import errno
import tempfile
import shutil
from . import result
from .case import TestCase
from .procs import xTracedProcess

TEMP_PREFIX = 'testres'

DEFAULT_CLEANUP = True
DEFAULT_SILENT = False


class BasicTestRunner(object):

    result_class = result.PrintedTestResult

    def __init__(self, result_class=None, **kwargs):
        self.options = kwargs

        if result_class is not None:
            self.result_class = result_class

        # Store the working directory.
        self.options['working_dir'] = os.getcwd()

    def _apply_options(self, obj):
        """Apply the appropriate options to the object"""
        obj.__marks_options__ = self.options

    def setup_environment(self):
        """Setup the environment before running the tests.

        Create a temporary directory to run tests from. Store location
        in options, so test cases can use this information.
        """
        working_dir = self.options['working_dir']
        if self.options.get('explain', False):
            # No temporary directory required, as no tests are run.
            temp_dir = working_dir
        else:
            # Create the temporary directory, as tests are being run.
            if not self.options.get('silent', DEFAULT_SILENT):
                print("Setting up environment...")

            # Create temporary working directory.
            prefix = self.options.get('temp_prefix', TEMP_PREFIX)
            temp_dir = tempfile.mkdtemp(dir=working_dir, prefix=prefix)

            if not self.options.get('cleanup', DEFAULT_CLEANUP):
                print("Test output in", temp_dir)
                print("Remember to clean up your test result folders.\n")

            # Change to new temp directory.
            os.chdir(temp_dir)

        # Store temporary directory path.
        self.options['temp_dir'] = temp_dir

    def tear_down_environment(self):
        """Tear down the environment after running the tests"""
        if not self.options.get('explain', False):
            # Only remove temporary directory if it was created.
            if not self.options.get('silent', DEFAULT_SILENT):
                print("Tearing down environment...")

            # Ensure we are in the original working directory.
            os.chdir(self.options['working_dir'])

            if self.options.get('cleanup', DEFAULT_CLEANUP):
                # Clean up the temporary folder.
                try:
                    shutil.rmtree(self.options['temp_dir'])
                except OSError as e:
                    # Check for ENOENT: "No such file or directory." - Nothing
                    # more to do if directory has already been deleted.
                    if e.errno != errno.ENOENT:
                        # Other error, so raise.
                        raise

    def run(self, test):
        # Setup the environment.
        self.setup_environment()

        # Apply the options to the test.
        self._apply_options(test)

        # Create the result holder.
        result = self.result_class()
        self._apply_options(result)

        # Run the test
        result.start_test_run()
        test.run(result)
        result.stop_test_run()

        # Tear down the environment.
        self.tear_down_environment()

        return result


class MarkingTestRunner(BasicTestRunner):

    result_class = result.MarkingTestResult

    def run(self, test):
        # Setup the environment.
        self.setup_environment()

        # Apply the options to the test.
        self._apply_options(test)

        # Set the TestCase to use a TracedProcess.
        TestCase.process_class = xTracedProcess

        # Create the result holder.
        result = self.result_class()
        self._apply_options(result)

        result.start_test_run()
        test.run(result)
        result.stop_test_run()

        # Print results
        if not self.options.get('silent', False):
            if self.options.get('verbose', False):
                print()
            print("Marking Results")
            print("{0:30}{1:15}{2}".format('Category', 'Passed', 'Mark'))
            for category in result.marks:
                info = result.marks[category]
                total = info['total_marks'] or info['category_marks']
                if total==0:
                    fraction = 0
                else:
                    fraction = info['mark'] / total
                print("{0:30}{1:15}{2:.2f}/{3:.2f} ({4:.2%})".format(
                    category,
                    '{0}/{1}'.format(info['passed'], len(info['tests'])),
                    info['mark'], total,
                    fraction))

            print("\n{0:30}{1:15}{2:.2f}/{3:.2f} ({4:.2%})".format(
                'Total',
                '{0}/{1}'.format(result.tests_passed, result.total_tests),
                result.received_marks, result.total_marks,
                result.received_marks / result.total_marks))

        # Tear down the environment
        self.tear_down_environment()

        return result


CONFIRMATION_MESSAGE = """
Please confirm that you want to update the output files in this test suite.

NOTE: THIS PROCESS WILL MODIFY EXISTING FILES.
      PLEASE ENSURE YOU HAVE A BACKUP BEFORE PROCEEDING.
"""


class UpdateTestRunner(BasicTestRunner):

    result_class = result.UpdateTestResult

    def run(self, test):
        # Confirm that the update should proceed.
        print(CONFIRMATION_MESSAGE)
        confirm = input("Are you sure you want to update the files? (y/N)")

        if confirm == 'y':
            # Set update flag.
            self.options['update'] = True
            super(UpdateTestRunner, self).run(test)
