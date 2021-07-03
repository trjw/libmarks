import argparse
import os
import sys
import multiprocessing as mp

from . import loader, runner, marking, result
from .version import get_version


class TestProgram(object):

    runner_class = runner.BasicTestRunner

    def __init__(
        self, module="__main__", test_loader=loader.default_test_loader, options=None
    ):
        if isinstance(module, str):  # was basestring in py2
            self.module = __import__(module)
            # Load the module at the correct level
            for part in module.split(".")[1:]:
                self.module = getattr(self.module, part)
        else:
            self.module = module

        self.test_loader = test_loader

        # Store options to be sent to the test runner.
        self.options = {}
        if options is not None:
            self.options = options

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
            "--version",
            action="version",
            version="%(prog)s {version}".format(version=get_version()),
        )

        subparsers = self._parser.add_subparsers()

        # Standard test parser.
        parser_test = subparsers.add_parser("test", help="Run test(s)")
        parser_test.add_argument(
            "tests",
            nargs="*",
            help="a list of any number of test modules, " "classes and test methods.",
        )
        parser_test.add_argument(
            "-s",
            "--save",
            dest="save_output",
            action="store_true",
            help="Save output from the test(s) being run",
        )
        parser_test.add_argument(
            "-v",
            "--verbose",
            dest="verbose",
            action="store_true",
            help="Show verbose output (incl. diff) for a test on failure",
        )
        parser_test.add_argument(
            "--fuzzy",
            dest="fuzzy",
            action="store_true",
            help="Whether or not to use fuzzy matching.",
        )
        parser_test.add_argument(
            "-o",
            "--option",
            dest="options",
            action="append",
            help="Set custom options for this test run.",
        )
        parser_test.set_defaults(func=self.set_up_test)

        # Explain parser.
        parser_explain = subparsers.add_parser(
            "explain", help="Explain what tests run and check"
        )
        parser_explain.add_argument(
            "tests",
            nargs="*",
            help="a list of any number of test modules, " "classes and test methods.",
        )
        parser_explain.add_argument(
            "-o",
            "--option",
            dest="options",
            action="append",
            help="Set custom options for this test run.",
        )
        parser_explain.set_defaults(func=self.set_up_explain)

        # Update parser.
        parser_update = subparsers.add_parser(
            "update", help="Update files associated with test(s)"
        )
        parser_update.add_argument(
            "tests",
            nargs="*",
            help="a list of any number of test modules, " "classes and test methods.",
        )
        parser_update.add_argument(
            "-o",
            "--option",
            dest="options",
            action="append",
            help="Set custom options for this test run.",
        )
        parser_update.set_defaults(func=self.set_up_update)

        # Marking parser.
        parser_mark = subparsers.add_parser(
            "mark", help="Run tests and calculate marks"
        )
        parser_mark.add_argument(
            "tests",
            nargs="*",
            help="a list of any number of test modules, " "classes and test methods.",
        )
        parser_mark.add_argument(
            "-v",
            "--verbose",
            dest="verbose",
            action="store_true",
            help="Show verbose output during marking",
        )
        parser_mark.add_argument(
            "--directory",
            dest="directory",
            help="Parent directory containing subdirectories for marking",
        )
        parser_mark.add_argument(
            "--processes",
            dest="processes",
            type=int,
            default=marking.NUM_PROCESSES,
            help="Number of processes to use during marking",
        )
        parser_mark.add_argument(
            "--resume",
            dest="resume",
            action="store_true",
            help="Resume marking from a previous attempt",
        )
        parser_mark.add_argument(
            "--tally",
            dest="tally",
            action="store_true",
            help="Tally the results from a previously marked directory",
        )
        parser_mark.add_argument(
            "--fuzzy",
            dest="fuzzy",
            action="store_true",
            help="Whether or not to use fuzzy matching",
        )
        parser_mark.add_argument(
            "-o",
            "--option",
            dest="options",
            action="append",
            help="Set custom options for this test run.",
        )
        parser_mark.set_defaults(func=self.set_up_mark)
        parser_mark.add_argument(
            "--random-order",
            action="store_true",
            help="Test submissions in random order",
        )

    def parse_arguments(self, argv):
        """Parse arguments received from the command line."""
        self._init_arg_parsers()
        args = self._parser.parse_args(argv[1:])

        # Process the arguments we received
        if not "func" in vars(args):
            self._parser.print_help()
            exit(0)
        args.func(args)
        self.parse_options(args)

    def initialise_marks(self, argv):
        """Initialise the marks system before running tests."""
        # Set up flag defaults
        self.options["cleanup"] = runner.DEFAULT_CLEANUP
        self.options["silent"] = runner.DEFAULT_SILENT

        # Parse arguments
        self.parse_arguments(argv)

        mp.set_start_method("spawn")
        # Create tests
        if self.tests:
            self.test_names = self.tests
            if __name__ == "__main__":
                self.module = None
        else:
            self.test_names = None
        self.create_tests()

    def set_up_test(self, args):
        """Set up system to run tests normally."""
        self.tests = args.tests
        self.options["save"] = args.save_output
        self.options["verbose"] = True
        self.options["fuzzy"] = args.fuzzy
        if args.save_output:
            self.options["cleanup"] = False
        if args.verbose:
            if args.tests:
                self.options["show_diff"] = True
            else:
                print("WARNING: Verbose mode ignored as no tests specified.")

    def set_up_explain(self, args):
        """Set up system to run simulation of tests (no processes run)."""
        self.tests = args.tests
        self.options["explain"] = True
        # Use the Detail result for a simulation.
        self.options["result_class"] = result.ExplainTestResult

    def set_up_update(self, args):
        """Set up system to run tests and update files they use."""
        # Perform file updates
        self.tests = args.tests
        self.options["update"] = True
        self.options["fuzzy"] = False
        self.runner_class = runner.UpdateTestRunner

    def set_up_mark(self, args):
        """Set up system to run tests and calculate a mark."""
        self.tests = args.tests
        self.options["fuzzy"] = args.fuzzy
        if args.directory:
            # Mark directory full of submissions.
            self.runner_class = marking.MarkingRunner
            self.options["directory"] = args.directory
            self.options["processes"] = args.processes
            self.options["resume"] = args.resume
            self.options["tally"] = args.tally
            self.options["random_order"] = args.random_order
        else:
            # Mark a single submission in the current directory.
            self.options["verbose"] = args.verbose
            self.runner_class = runner.MarkingTestRunner

    def parse_options(self, args):
        """Add custom options from the command line to the test option set.

        Do not override existing options set during configuration.
        """
        if args.options:
            for opt in args.options:
                name = opt
                val = True
                if "=" in opt:
                    name, val = opt.split("=")
                if name not in self.options:
                    self.options[name] = val

    def create_tests(self):
        """Create a list of tests to be run."""
        if self.test_names is None:
            self.test = self.test_loader.load_tests_from_module(self.module)
        else:
            self.test = self.test_loader.load_tests_from_names(
                self.test_names, self.module
            )

    def run_tests(self):
        """Run the tests using the appropriate settings."""
        runner = self.runner_class(**self.options)
        try:
            runner.run(self.test)
        except KeyboardInterrupt:
            # Clean up environment before exiting.
            runner.tear_down_environment()
            raise


main = TestProgram
