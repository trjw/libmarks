import argparse
import os
import sys

from . import loader, runner


class TestProgram(object):

    runner_class = runner.BasicTestRunner

    def __init__(
            self, module='__main__', test_loader=loader.default_test_loader,
            flags=None):
        if isinstance(module, basestring):
            self.module = __import__(module)
            # Load the module at the correct level
            for part in module.split('.')[1:]:
                self.module = getattr(self.module, part)
        else:
            self.module = module

        self.test_loader = test_loader

        # Store flags to be sent to the test runner.
        self.flags = {}
        if flags is not None:
            self.flags = flags

        argv = sys.argv

        self.prog_name = os.path.basename(argv[0])
        self.parse_arguments(argv)
        self.run_tests()

    def _init_arg_parsers(self):
        parser = argparse.ArgumentParser()
        parser.prog = self.prog_name

        parser.add_argument('tests', nargs='*',
                            help='a list of any number of test modules, '
                            'classes and test methods.')

        parser.add_argument('-m', '--mark', dest='mark', action='store_true',
                            help=argparse.SUPPRESS)

        parser.add_argument('--update', dest='update', action='store_true',
                            help=argparse.SUPPRESS)

        parser.add_argument('-d', '--detail', dest='detail',
                            action='store_true',
                            help='Show details for the test(s) being run')

        self._parser = parser

    def parse_arguments(self, argv):
        self._init_arg_parsers()
        self._parser.parse_args(argv[1:], self)

        if self.tests:
            self.test_names = self.tests
            if __name__ == '__main__':
                self.module = None
        else:
            self.test_names = None
        self.create_tests()

        if self.mark:
            # Perform marking
            self.runner_class = runner.MarkingTestRunner
        elif self.update:
            # Perform file updates
            self.runner_class = runner.UpdateTestRunner
        elif self.detail:
            # Run detail mode
            self.runner_class = runner.DetailTestRunner

    def create_tests(self):
        if self.test_names is None:
            self.test = self.test_loader.load_tests_from_module(self.module)
        else:
            self.test = self.test_loader.load_tests_from_names(
                self.test_names, self.module)

    def run_tests(self):
        runner = self.runner_class(**self.flags)
        runner.run(self.test)


main = TestProgram
