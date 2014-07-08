#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <csignal>
#include <unistd.h>
#include <sys/wait.h>
#include <fcntl.h>

#include "process.hpp"

/* Public */
Process::Process(std::vector<std::string> argv, std::string inputFile):
    input(NULL), output(NULL), error(NULL), finished(false),
    abnormalExit(false), signalled(false)
{
    init(argv, inputFile);
}

Process::Process(std::vector<std::string> argv):
    input(NULL), output(NULL), error(NULL), finished(false),
    abnormalExit(false), signalled(false)
{
    init(argv);
}

Process::~Process()
{
    if (!finished) {
        send_kill();
    }
}

bool Process::send(const std::string& message)
{
    if (input == NULL) {
        // No input pipe (pipe was not created, as input file was specified).
        return false;
    }

    if (fprintf(input, "%s", message.c_str()) != message.length()) {
        // Sending failed.
        return false;
    }

    // Ensure input is sent to child.
    fflush(input);

    // Full message was sent.
    return true;
}

bool Process::send_file(char *filePath)
{
    if (input == NULL) {
        // No input pipe (pipe was not created, as input file was specified).
        return false;
    }

    std::ifstream data (filePath);

    // Write the contents of the file to the program.
    data.close();
    return false;
}

bool Process::finish_input()
{
    if (input == NULL) {
        // No input pipe (pipe was not created, as input file was specified).
        return false;
    }

    return close_stream(&input);
}

bool Process::expect_stdout(const std::string& expected)
{
    return expect(expected, output);
}

bool Process::expect_stderr(const std::string& expected)
{
    return expect(expected, error);
}

bool Process::expect_stdout_file(char *filePath)
{
    return expect_file(filePath, output);
}

bool Process::expect_stderr_file(char *filePath)
{
    return expect_file(filePath, error);
}

std::string Process::readline_stdout()
{
    return readline(output);
}

std::string Process::readline_stderr()
{
    return readline(error);
}

void Process::print_stdout()
{
    print_stream(output);
}

void Process::print_stderr()
{
    print_stream(error);
}

bool Process::assert_exit_status(int expected)
{
    if (!finished)
        perform_wait(true);
    return !abnormalExit && exitStatus == expected;
}

bool Process::assert_signalled(bool expected)
{
    if (!finished)
        perform_wait(true);
    return signalled == expected;
}

bool Process::assert_signal(int expected)
{
    if (!finished)
        perform_wait(true);
    return signalled && signalNum == expected;
}

int Process::get_exit_status()
{
    return exitStatus;
}

bool Process::get_abnormal_exit()
{
    return abnormalExit;
}

bool Process::get_signalled()
{
    return signalled;
}

int Process::get_signal()
{
    return signalNum;
}

void Process::send_signal(int signalVal)
{
    // TODO: Check range allowed for child pid
    if (childPid <= 0 || kill(childPid, signalVal) == -1) {
        // TODO: raise exception on failure
        throw SignalException();
    }
}

void Process::send_kill()
{
    if (!finished) {
        send_signal(SIGKILL);
        perform_wait(true);
    }
}

/**
 * Check if the child process was signalled, via a non-blocking call to
 * `waitpid`.
 * @return true if process is finished and was signalled, false otherwise.
 */
bool Process::check_signalled()
{
    perform_wait(false);
    return finished && signalled;
}

/* Private */
void Process::init(std::vector<std::string> argv, std::string inputFile)
{
    bool useInputPipe = inputFile == "";

    // Create pipe for stdin only if there is no input file.
    if (useInputPipe && pipe(fdIn) != 0) {
        throw PipeException();
    }

    // Create the remaining pipes.
    if (pipe(fdOut) != 0 || pipe(fdErr) != 0 || pipe(fdCheck) != 0) {
        throw PipeException();
    }

    // Fork
    childPid = fork();

    if (childPid < 0) {
        throw ForkException();
    } else if (childPid == 0) {
        // Child process.
        setup_child(argv, inputFile);
    } else {
        // Parent process.
        setup_parent(useInputPipe);
    }
}

void Process::init(std::vector<std::string> argv)
{
    init(argv, "");
}

void Process::setup_parent(bool useInputPipe)
{
    // Close the ends of the pipes that are being used in the child.
    if ((useInputPipe && close(fdIn[READ]) == -1) ||
            close(fdOut[WRITE]) == -1 || close(fdErr[WRITE]) == -1 ||
            close(fdCheck[WRITE]) == -1) {
        throw CloseException();
    }

    // Attempt to read on check pipe. If data is available, then exec failed.
    char buf[5];
    if (read(fdCheck[READ], buf, 5) != 0) {
        perform_wait(true);
        throw ExecException();
    }

    // Close the check pipe, now we are finished with it.
    if (close(fdCheck[READ]) == -1)
        throw CloseException();

    // Open child stdin as a file, if pipe was created.
    if (useInputPipe) {
        input = fdopen(fdIn[WRITE], "w"); // Input from parent to child.
    }

    // Open the remaining pipes as files, for ease of use.
    output = fdopen(fdOut[READ], "r"); // stdout from child to parent.
    error = fdopen(fdErr[READ], "r"); // stderr from child to parent.

    if ((useInputPipe && input == NULL) || output == NULL || error == NULL) {
        throw FdOpenException();
    }
}

void Process::setup_child(std::vector<std::string> argv, std::string inputFile)
{
    bool do_exec = true;

    // Set up child input (stdin)
    if (inputFile != "") {
        // Open file as stdin for child.
        int fd = open(inputFile.c_str(), O_RDONLY);
        if (fd == -1 || dup2(fd, STDIN_FILENO) == -1 || close(fd) == -1) {
            do_exec = false;
        }
    } else {
        // Finish pipe creation.
        if (close(fdIn[WRITE]) == -1 ||
                dup2(fdIn[READ], STDIN_FILENO) == -1 ||
                close(fdIn[READ]) == -1) {
            do_exec = false;
        }
    }

    // Set up child output (stdout).
    if (close(fdOut[READ]) == -1 ||
            dup2(fdOut[WRITE], STDOUT_FILENO) == -1 ||
            close(fdOut[WRITE]) == -1) {
        do_exec = false;
    }

    // Set up child error (stderr).
    if (close(fdErr[READ]) == -1 ||
            dup2(fdErr[WRITE], STDERR_FILENO) == -1 ||
            close(fdErr[WRITE]) == -1) {
        do_exec = false;
    }

    if (close(fdCheck[READ]) == -1)
        do_exec = false;

    // Set up close-on-exec for the check pipe.
    int flags = fcntl(fdCheck[WRITE], F_GETFD);
    if (flags == -1)
        do_exec = false;

    flags |= FD_CLOEXEC;

    if (fcntl(fdCheck[WRITE], F_SETFD, flags) == -1)
        do_exec = false;

    // Execute the program.
    if (do_exec) {
        char **args = create_args(argv);
        execvp(args[0], args);

        delete_args(args, argv.size());
    }

    // Exec failed if program reaches this point.
    write(fdCheck[WRITE], "fail", 4);
    close(fdCheck[WRITE]);
    exit(-1);
}

char **Process::create_args(std::vector<std::string> argv)
{
    // Create args array, including space for the NULL array terminator.
    char **args = new char*[argv.size() + 1];

    // Copy the args to the new array.
    for(size_t i = 0; i < argv.size(); i++){
        args[i] = new char[argv[i].length() + 1];
        strcpy(args[i], argv[i].c_str());
    }

    // argv array for exec* needs to be null terminated.
    args[argv.size()] = NULL;

    return args;
}

void Process::delete_args(char **args, size_t length)
{
    // Count to length + 1, to accommodate NULL array terminator.
    for (int i = 0; i < length + 1; ++i) {
        delete [] args[i];
    }
    delete [] args;
}

bool Process::expect_file(char *filePath, FILE *stream)
{
    std::ifstream expectedOutput (filePath);

    if (!expectedOutput.is_open()) {
        // TODO: Raise error - error opening file
        throw StreamException();
    }

    char expected, received;

    // Char by char, check expected output against received output.
    do {
        expected = expectedOutput.get();
        received = fgetc(stream);
    } while (expectedOutput.good() && received != EOF && !feof(stream) &&
            expected == received);

    // If output was same as expected, then both should be at end of file.
    if (expectedOutput.eof() && feof(stream)) {
        expectedOutput.close();
        return true;
    }

    expectedOutput.close();
    return false;
}

bool Process::expect(const std::string& expected, FILE *stream)
{
    if (expected.length() == 0) {
        // TODO: Should this raise an exception?
        return false;
    }

    for (int i = 0; i < expected.length(); ++i) {
        if (expected[i] != (char) fgetc(stream)) {
            return false;
        }
    }

    return true;
}

std::string Process::readline(FILE *stream)
{
    std::string line;
    char c;

    while((c = fgetc(stream)) != EOF && !feof(stream) && c != '\n')
        line += c;

    return line;
}

void Process::print_stream(FILE *stream)
{
    char *buf = new char[80];

    while (stream != NULL && !feof(stream)) {
        if (fgets(buf, 80, stream) == NULL)
            break;
        std::cout << buf;
    }

    delete [] buf;
}

bool Process::close_stream(FILE **stream)
{
    int status = 0;
    if (*stream != NULL) {
        status = fclose(*stream);
        *stream = NULL;
    }

    if (status != 0) {
        return false;
    }

    return true;
}

void Process::perform_wait(bool block)
{
    if (!finished) {
        // Set up options for waitpid, based on whether we should wait
        // for the process to complete or not.
        int options = 0;
        if (!block) {
            options = WNOHANG;
        }

        // Wait on the child and reap it once it is complete.
        int status;
        int result = waitpid(childPid, &status, options);

        if (!block && result == 0) {
            // Child is not finished, so do not check status.
            return;
        }

        // TODO: Check for other results of waitpid.

        // Check for the exit status of the child
        if (WIFEXITED(status)) {
            exitStatus = WEXITSTATUS(status);
        } else {
            abnormalExit = true;
        }

        if (WIFSIGNALED(status)) {
            signalled = true;
            signalNum = WTERMSIG(status);
        }

        // Close the files.
        close_stream(&input);
        close_stream(&output);
        close_stream(&error);

        finished = true;
    }
}
