from __future__ import division, print_function
import sys
from .util import safe_repr, coloured_text
from .process import Process as _Process
from .process import TracedProcess as _TracedProcess
from .process import TimeoutProcess as _TimeoutProcess


class xProcess(object):
    def __init__(self, argv, *vec, **kwargs):
        input_file = kwargs.get("input_file", None)
        if input_file is None:
            self._proc = _Process(argv)
        else:
            self._proc = _Process(argv, input_file)
        self._setup_attributes()

    def _setup_attributes(self):
        self.pid = self._proc.pid
        self.exit_status = self._proc.exit_status
        self.abnormal_exit = self._proc.abnormal_exit
        self.signalled = self._proc.signalled
        self.signal = self._proc.signal
        self.timeout = self._proc.timeout

    def send(self, message, **kwargs):
        self._proc.send(message)

    def send_file(self, fname, **kwargs):
        self._proc.send_file(fname)

    def finish_input(self, **kwargs):
        self._proc.finish_input()

    def expect_stdout(self, text, **kwargs):
        return self._proc.expect_stdout(text)

    def expect_stderr(self, text, **kwargs):
        return self._proc.expect_stderr(text)

    def expect_stdout_file(self, fname, **kwargs):
        return self._proc.expect_stdout_file(fname)

    def expect_stderr_file(self, fname, **kwargs):
        return self._proc.expect_stderr_file(fname)

    def readline_stdout(self, **kwargs):
        return self._proc.readline_stdout()

    def readline_stderr(self, **kwargs):
        return self._proc.readline_stderr()

    def print_stdout(self, **kwargs):
        return self._proc.print_stdout()

    def print_stderr(self, **kwargs):
        return self._proc.print_stderr()

    def assert_exit_status(self, status, **kwargs):
        return self._proc.assert_exit_status(status)

    def assert_signalled(self, tf, **kwargs):
        return self._proc.assert_signalled(tf)

    def assert_signal(self, sig, **kwargs):
        return self._proc.assert_signal(sig)

    def send_signal(self, sig, **kwargs):
        self._proc.send_signal(sig)

    def send_signal_group(self, sig, **kwargs):
        self._proc.send_signal_group(sig)

    def kill(self, **kwargs):
        self._proc.kill()

    def check_signalled(self, **kwargs):
        return self._proc.check_signalled()


class xTracedProcess(xProcess):
    def __init__(self, argv, *vec, **kwargs):
        timeout = kwargs.get("timeout", None)
        input_file = kwargs.get("input_file", None)
        if timeout is None:
            raise ValueError("timeout keyword arg required")
        if input_file is None:
            self._proc = _TracedProcess(argv, timeout)
        else:
            self._proc = _TracedProcess(argv, timeout, input_file)
        self._setup_attributes()


class xTimeoutProcess(xProcess):
    def __init__(self, argv, *vec, **kwargs):
        timeout = kwargs.get("timeout", None)
        input_file = kwargs.get("input_file", None)
        if timeout is None:
            raise ValueError("timeout keyword arg required")
        if input_file is None:
            self._proc = _TimeoutProcess(argv, timeout)
        else:
            self._proc = _TimeoutProcess(argv, timeout, input_file)
        self._setup_attributes()


class ExplainProcess(object):

    """A dummy process class, for use with the explain test functionality"""

    def __init__(self, argv, input_file=None, **kwargs):
        self.argv = argv
        self.input_file = input_file
        self.count = -1

        # Count how many times a message is sent.
        self._send_count = 0

    def _print_coloured(self, text, fg=None, bg=None, attrs=None, **kwargs):
        stream = kwargs.get("file", sys.stdout)
        if stream.isatty():
            # Only add colours and attributes if stream is a TTY.
            text = coloured_text(text, colour=fg, background=bg, attrs=attrs)
        print(text, **kwargs)

    def finish_input(self, **kwargs):
        self._print_coloured(
            f"Finish input to Process {self.count} (ie. Ctrl+D)", attrs=["bold"]
        )

    def kill(self, **kwargs):
        self._print_coloured(f"Kill Process {self.count}", attrs=["bold"], end="")
        print(" (send SIGKILL to process group)")

    def readline_stderr(self, **kwargs):
        if "explain" in kwargs:
            self._print_coloured(kwargs["explain"], attrs=["bold"], end="\n")
        else:
            self._print_coloured(
                f"Read line from stderr of Process {self.count}",
                attrs=["bold"],
                end="\n",
            )
        return ""

    def readline_stdout(self, **kwargs):
        if "explain" in kwargs:
            self._print_coloured(kwargs["explain"], attrs=["bold"], end="\n")
        else:
            self._print_coloured(
                f"Read line from stdout of Process {self.count}",
                attrs=["bold"],
                end="\n",
            )
        return ""

    def send(self, message, **kwargs):
        if "explain" in kwargs:
            self._print_coloured(kwargs["explain"], attrs=["bold"], end="\n")
            return
        # Print out the first 10 messages that are sent to the process.
        if self._send_count < 11:
            # Show what is being sent to the process.
            self._print_coloured(
                f"Send input to Process {self.count}: ", attrs=["bold"], end=""
            )
            print(safe_repr(message))
        elif self._send_count == 11:
            # Instruct user to read test case, as lots of input being sent.
            self._print_coloured(
                f"Further input sent to Process {self.count} -"
                " see test case for details",
                attrs=["bold"],
            )

        self._send_count += 1

    def print_stdout(self, **kwargs):
        if "explain" in kwargs:
            self._print_coloured(kwargs["explain"], attrs=["bold"], end="\n")
        else:
            self._print_coloured(
                f"Dump the remainer of stdout ofof Process {self.count}: ",
                attrs=["bold"],
                end="",
            )
        pass

    def print_stderr(self, **kwargs):
        if "explain" in kwargs:
            self._print_coloured(kwargs["explain"], attrs=["bold"], end="\n")
        else:
            self._print_coloured(
                f"Dump the remainder of stderr of Process {self.count}: ",
                attrs=["bold"],
                end="",
            )
        pass

    def send_signal(self, signal, **kwargs):
        if "explain" in kwargs:
            self._print_coloured(kwargs["explain"], attrs=["bold"], end="\n")
            return
        # Print out the signal being sent to the process.
        self._print_coloured(
            f"Send signal to Process {self.count}: ", attrs=["bold"], end=""
        )
        print(signal)

    def send_signal_group(self, signal, **kwargs):
        if "explain" in kwargs:
            self._print_coloured(kwargs["explain"], attrs=["bold"], end="\n")
            return
        # Print out the signal being sent to the process group.
        self._print_coloured(
            f"Send signal to Process {self.count} (incl. children): ",
            attrs=["bold"],
            end="",
        )
        print(signal)

    def assert_exit_status(self, status, **kwargs):
        if "explain" in kwargs:
            self._print_coloured(kwargs["explain"], attrs=["bold"], end="\n")
            return
        # Print out the signal being sent to the process.
        self._print_coloured(
            f"Exit status for Process {self.count}: {status}?",
            attrs=["bold"],
            end="\n",
        )

    def assert_signalled(self, tf, **kwargs):
        if "explain" in kwargs:
            self._print_coloured(kwargs["explain"], attrs=["bold"], end="\n")
            return
        # Print out the signal being sent to the process.
        self._print_coloured(
            f"Process {self.count} was signalled: {tf}?",
            attrs=["bold"],
            end="\n",
        )

    def assert_signal(self, sig, **kwargs):
        if "explain" in kwargs:
            self._print_coloured(kwargs["explain"], attrs=["bold"], end="\n")
            return
        # Print out the signal being sent to the process.
        self._print_coloured(
            f"Did Process {self.count} receive signal {sig}?",
            attrs=["bold"],
            end="\n",
        )

    def kill(self, **kwargs):
        if "explain" in kwargs:
            self._print_coloured(kwargs["explain"], attrs=["bold"], end="\n")
            return
        # Print out the signal being sent to the process.
        self._print_coloured(f"Kill Process {self.count}.", attrs=["bold"], end="\n")

    def check_signalled(self, **kwargs):
        if "explain" in kwargs:
            self._print_coloured(kwargs["explain"], attrs=["bold"], end="\n")
            return
        # Print out the signal being sent to the process.
        self._print_coloured(
            f"Was Process {self.count} signalled?", attrs=["bold"], end="\n"
        )
