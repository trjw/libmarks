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
        print("{:30}{:15}{}".format('Category', 'Passed', 'Mark'))
        for category in result.marks:
            info = result.marks[category]
            total = info['total_marks'] or info['category_marks']
            print("{:30}{:15}{:.2f}/{:.2f} ({:.2%})".format(
                category,
                '{}/{}'.format(info['passed'], len(info['tests'])),
                info['mark'], total,
                info['mark'] / total))

        print("\n{:30}{:15}{:.2f}/{:.2f} ({:.2%})".format(
            'Total',
            '{}/{}'.format(result.tests_passed, result.total_tests),
            result.received_marks, result.total_marks,
            result.received_marks / result.total_marks))

        return result


class DetailTestRunner(BasicTestRunner):

    result_class = result.DetailTestResult

    def run(self, test):
        # Set details flag.
        test.__marks_details__ = True
        super(DetailTestRunner, self).run(test)
