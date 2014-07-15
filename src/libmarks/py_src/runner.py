from . import result


class BasicTestRunner(object):

    result_class = result.PrintedTestResult

    def run(self, test):
        result = self.result_class()

        result.start_test_run()
        test.run(result)
        result.stop_test_run()
        return result
