import argparse
import os
import sys

from . import loader, runner, marking, result
from ._version import get_version


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
        self.initialise_marks(argv)
        self.run_tests()

    def _init_arg_parsers(self):
        """Initialise the argument parser.

        Uses subcommand structure to separate functions into distinct modes.
        """
        self._parser = argparse.ArgumentParser()
        self._parser.prog = self.prog_name

        self._parser.add_argument(
            '--version', action='version',
            version='%(prog)s {version}'.format(version=get_version()))

        subparsers = self._parser.add_subparsers()

        # Standard test parser.
        parser_test = subparsers.add_parser(
            'test', help='Run test(s)')
        parser_test.add_argument(
            'tests', nargs='*', help='a list of any number of test modules, '
            'classes and test methods.')
        parser_test.add_argument(
            '-s', '--save', dest='save_output', action='store_true',
            help='Save output from the test(s) being run')
        parser_test.set_defaults(func=self.set_up_test)

        # Simulation parser.
        parser_simulate = subparsers.add_parser(
            'simulate', help='Simulate running test(s)')
        parser_simulate.add_argument(
            'tests', nargs='*', help='a list of any number of test modules, '
            'classes and test methods.')
        parser_simulate.set_defaults(func=self.set_up_simulate)

        # Update parser.
        parser_update = subparsers.add_parser(
            'update', help='Update files associated with test(s)')
        parser_update.add_argument(
            'tests', nargs='*', help='a list of any number of test modules, '
            'classes and test methods.')
        parser_update.set_defaults(func=self.set_up_update)

        # Marking parser.
        parser_mark = subparsers.add_parser(
            'mark', help='Run tests and calculate marks')
        parser_mark.add_argument(
            'tests', nargs='*', help='a list of any number of test modules, '
            'classes and test methods.')
        parser_mark.add_argument(
            '--directory', dest='directory',
            help='Parent directory containing subdirectories for marking')
        parser_mark.add_argument(
            '--processes', dest='processes', type=int,
            default=marking.NUM_PROCESSES,
            help='Number of processes to use during marking')
        parser_mark.set_defaults(func=self.set_up_mark)

    def parse_arguments(self, argv):
        """Parse arguments received from the command line."""
        self._init_arg_parsers()
        args = self._parser.parse_args(argv[1:])
        # Process the arguments we received
        args.func(args)

    def initialise_marks(self, argv):
        """Initialise the marks system before running tests."""
        # Set up flag defaults
        self.flags['cleanup'] = runner.DEFAULT_CLEANUP
        self.flags['silent'] = runner.DEFAULT_SILENT

        # Parse arguments
        self.parse_arguments(argv)

        # Create tests
        if self.tests:
            self.test_names = self.tests
            if __name__ == '__main__':
                self.module = None
        else:
            self.test_names = None
        self.create_tests()

    def set_up_test(self, args):
        """Set up system to run tests normally."""
        self.tests = args.tests
        self.flags['save'] = args.save_output
        if args.save_output:
            self.flags['cleanup'] = False

    def set_up_simulate(self, args):
        """Set up system to run simulation of tests (no processes run)."""
        self.tests = args.tests
        self.flags['simulate'] = True
        # Use the Detail result for a simulation.
        self.flags['result_class'] = result.DetailTestResult

    def set_up_update(self, args):
        """Set up system to run tests and update files they use."""
        # Perform file updates
        self.tests = args.tests
        self.flags['update'] = True
        self.runner_class = runner.UpdateTestRunner

    def set_up_mark(self, args):
        """Set up system to run tests and calculate a mark."""
        self.tests = args.tests
        if args.directory:
            # Mark directory full of submissions.
            self.runner_class = marking.MarkingRunner
            self.flags['directory'] = args.directory
            self.flags['processes'] = args.processes
        else:
            # Mark a single submission in the current directory.
            self.runner_class = runner.MarkingTestRunner

    def create_tests(self):
        """Create a list of tests to be run."""
        if self.test_names is None:
            self.test = self.test_loader.load_tests_from_module(self.module)
        else:
            self.test = self.test_loader.load_tests_from_names(
                self.test_names, self.module)

    def run_tests(self):
        """Run the tests using the appropriate settings."""
        runner = self.runner_class(**self.flags)
        runner.run(self.test)


main = TestProgram
