from __future__ import division, print_function
from . import result


class BasicTestRunner(object):

    result_class = result.PrintedTestResult

    def run(self, test):
        result = self.result_class()

        result.start_test_run()
        test.run(result)
        result.stop_test_run()
        return result


class MarkingTestRunner(BasicTestRunner):

    result_class = result.MarkingTestResult

    def run(self, test):
        result = self.result_class()

        result.start_test_run()
        test.run(result)
        result.stop_test_run()

        # Print results
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

        return result


CONFIRMATION_MESSAGE = """
Please confirm that you want to update the output files in this test suite.

NOTE: THIS PROCESS WILL MODIFY EXISTING FILES.
      PLEASE ENSURE YOU HAVE A BACKUP BEFORE PROCEEDING.
"""


class UpdateTestRunner(BasicTestRunner):

    result_class = result.UpdateTestResult

    def run(self, test):
        # Confirm that the update should proceed
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
