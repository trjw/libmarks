#!/usr/bin/env python3
import os
import pathlib
import sys

LIBMARKS_ROOT = str(pathlib.Path.home() / "libmarks-root")
TEST_LOCATION = str(pathlib.Path(__file__).resolve().parent / "tests")

sys.path[0:0] = [LIBMARKS_ROOT]
import marks


class LibmarksSampleTests(marks.TestCase):
    timeout = 2

    @classmethod
    def setup_class(cls):
        options = getattr(cls, "__marks_options__", {})

        working_root = pathlib.Path(options["working_dir"]).resolve()
        temp_root = pathlib.Path(options["temp_dir"]).resolve()

        cls.helloworld = str(working_root / "helloworld.py")

        # Create symlink to tests in working directory
        os.chdir(str(working_root))
        try:
            pathlib.Path("tests").symlink_to(TEST_LOCATION)
        except OSError:
            pass
        os.chdir(str(temp_root))

        # Modify test environment when running tests
        if not options.get("explain", False):

            # Compile the programs (if needed)
            os.chdir(str(working_root))
            # p = marks.Process(["make"])
            os.chdir(str(temp_root))

            # Don't run tests if compilation fails
            # assert p.assert_exit_status(0)

            # Create symlink to tests in temp directory
            try:
                pathlib.Path("tests").symlink_to(TEST_LOCATION)
            except OSError:
                pass

    @marks.marks(category="fail-check", category_marks=5)
    def test_raiseFail(self):
        """
        Check that failure assertions work
        """
        self.fail("Failure raised successfully")

    @marks.marks(category="stdout-check", category_marks=5)
    def test_stdoutFileMatchExact(self):
        """
        Check that comparing stdout to a file works
        correctly when the files match exactly
        """
        proc = self.process([self.helloworld])
        self.assert_stdout_matches_file(proc, "tests/helloworld.out")

    @marks.marks(category="stdout-check", category_marks=5)
    def test_stdoutFileMatchDifferent(self):
        """
        Check that comparing stdout to a file works
        correctly when the files don't match exactly
        """
        proc = self.process([self.helloworld, "--lower"])
        self.assert_stdout_matches_file(proc, "tests/helloworld.out")

    @marks.marks(category="stderr-check", category_marks=5)
    def test_stderrFileMatchExact(self):
        """
        Check that comparing stderr to a file works
        correctly when the files match exactly
        """
        proc = self.process([self.helloworld, "--stderr"])
        self.assert_stderr_matches_file(proc, "tests/helloworld.out")

    @marks.marks(category="stderr-check", category_marks=5)
    def test_stderrFileMatchDifferent(self):
        """
        Check that comparing stderr to a file works
        correctly when the files don't match exactly
        """
        proc = self.process([self.helloworld, "--lower", "--stderr"])
        self.assert_stderr_matches_file(proc, "tests/helloworld.out")

    @marks.marks(category="stdout-check", category_marks=5)
    def test_stdoutStringMatchExact(self):
        """
        Check that comparing stdout to a string works
        correctly when the files match exactly
        """
        proc = self.process([self.helloworld])
        self.assert_stdout(proc, "HELLO world")

    @marks.marks(category="stdout-check", category_marks=5)
    def test_stdoutStringMatchDifferent(self):
        """
        Check that comparing stdout to a string works
        correctly when the files don't match exactly
        """
        proc = self.process([self.helloworld, "--lower"])
        self.assert_stdout(proc, "HELLO world")

    @marks.marks(category="stderr-check", category_marks=5)
    def test_stderrStringMatchExact(self):
        """
        Check that comparing stderr to a string works
        correctly when the files match exactly
        """
        proc = self.process([self.helloworld, "--stderr"])
        self.assert_stderr(proc, "HELLO world")

    @marks.marks(category="stderr-check", category_marks=5)
    def test_stderrStringMatchDifferent(self):
        """
        Check that comparing stderr to a string works
        correctly when the files don't match exactly
        """
        proc = self.process([self.helloworld, "--lower", "--stderr"])
        self.assert_stderr(proc, "HELLO world")

    @marks.marks(category="return-code-check", category_marks=5)
    def test_returnCodeMatch(self):
        """
        Check that the return code check works
        correctly when the code matches exactly
        """
        proc = self.process([self.helloworld])
        self.assert_exit_status(proc, 0)

    @marks.marks(category="return-code-check", category_marks=5)
    def test_returnCodeDifferent(self):
        """
        Check that the return code check works
        correctly when the code doesn't match
        """
        proc = self.process([self.helloworld, "--returncode", "1"])
        self.assert_exit_status(proc, 0)

    @marks.marks(category="timeout-check", category_marks=5)
    def test_timeout1(self):
        """
        Check that the timeout works correctly
        """
        proc = self.process([self.helloworld, "--timeout"])
        self.assert_stdout_matches_file(proc, "tests/helloworld.out")

    @marks.marks(category="timeout-check", category_marks=5)
    def test_timeout2(self):
        """
        Check that the timeout works correctly
        """
        proc = self.process([self.helloworld, "--timeout"])
        self.assert_stderr_matches_file(proc, "tests/helloworld.out")

    @marks.marks(category="timeout-check", category_marks=5)
    def test_timeout3(self):
        """
        Check that the timeout works correctly
        """
        proc = self.process([self.helloworld, "--timeout"])
        self.assert_stdout(proc, "hello WORLD")

    @marks.marks(category="timeout-check", category_marks=5)
    def test_timeout4(self):
        """
        Check that the timeout works correctly
        """
        proc = self.process([self.helloworld, "--timeout"])
        self.assert_stderr(proc, "hello WORLD")

    @marks.marks(category="timeout-check", category_marks=5)
    def test_timeout5(self):
        """
        Check that the timeout works correctly
        """
        proc = self.process([self.helloworld, "--timeout"])
        self.assert_exit_status(proc, 0)


if __name__ == "__main__":
    marks.main()
