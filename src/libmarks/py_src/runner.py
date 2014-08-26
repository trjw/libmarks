from __future__ import division, print_function
import os
import errno
import tempfile
import shutil
from . import result

TEMP_PREFIX = 'testres'


class BasicTestRunner(object):

    result_class = result.PrintedTestResult

    def __init__(self, result_class=None, **kwargs):
        self.flags = kwargs

        if result_class is not None:
            self.result_class = result_class

        # Store the working directory.
        self.flags['working_dir'] = os.getcwd()

    def _apply_flags(self, test):
        """Apply the appropriate flags to the tests"""
        test.__marks_flags__ = self.flags

    def setup_environment(self):
        """Setup the environment before running the tests.

        Create a temporary directory to run tests from. Store location
        in flags, so test cases can use this information.
        """
        working_dir = self.flags['working_dir']
        prefix = self.flags.get('temp_prefix', TEMP_PREFIX)

        # Create temporary working directory.
        temp_dir = tempfile.mkdtemp(dir=working_dir, prefix=prefix)

        if not self.flags.get('silent', False):
            print("Test output in", temp_dir)
            print("Remember to clean up your test result folders.\n")

        # Change to new temp directory.
        os.chdir(temp_dir)

        # Store temporary directory path.
        self.flags['temp_dir'] = temp_dir

    def tear_down_environment(self):
        """Tear down the environment after running the tests"""
        if self.flags.get('cleanup', False):
            try:
                shutil.rmtree(self.flags['temp_dir'])
            except OSError as e:
                # Check for ENOENT: No such file or directory.
                # (Nothing more to do if directory has already been deleted)
                if e.errno != errno.ENOENT:
                    # Other error, so raise.
                    raise

    def run(self, test):
        # Setup the environment.
        self.setup_environment()

        # Apply the flags to the test.
        self._apply_flags(test)

        # Create the result holder.
        result = self.result_class()

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

        # Apply the flags to the test.
        self._apply_flags(test)

        # Create the result holder.
        result = self.result_class()

        result.start_test_run()
        test.run(result)
        result.stop_test_run()

        # Print results
        if not self.flags.get('silent', False):
            print("{0:30}{1:15}{2}".format('Category', 'Passed', 'Mark'))
            for category in result.marks:
                info = result.marks[category]
                total = info['total_marks'] or info['category_marks']
                print("{0:30}{1:15}{2:.2f}/{3:.2f} ({4:.2%})".format(
                    category,
                    '{0}/{1}'.format(info['passed'], len(info['tests'])),
                    info['mark'], total,
                    info['mark'] / total))

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
        confirm = raw_input("Are you sure you want to update the files? (y/N)")

        if confirm == 'y':
            # Set update flag.
            test.__marks_update__ = True
            super(UpdateTestRunner, self).run(test)


class DetailTestRunner(BasicTestRunner):

    result_class = result.DetailTestResult

    def run(self, test):
        # Set details flag.
        test.__marks_details__ = True
        super(DetailTestRunner, self).run(test)
