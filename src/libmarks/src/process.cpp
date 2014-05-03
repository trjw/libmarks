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
Process::Process(std::vector<std::string> argv):
    input(NULL), output(NULL), error(NULL), finished(false),
    abnormalExit(false), signalled(false)
{
    // Create pipes
    if (pipe(fdIn) != 0 || pipe(fdOut) != 0 ||
            pipe(fdErr) != 0 || pipe(fdCheck) != 0) {
        throw 1;
    }

    // Fork
    childPid = fork();

    if (childPid < 0) {
        throw 1;
    } else if (childPid == 0) {
        // Child process.
        setup_child(argv);
    } else {
        // Parent process.
        setup_parent();
    }
}

Process::~Process()
{
    if (!finished) {
        send_kill();
    }
}

bool Process::send(const std::string& message)
{
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
    std::ifstream data (filePath);

    // Write the contents of the file to the program.
    data.close();
    return false;
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
        perform_wait();
    return !abnormalExit && exitStatus == expected;
}

bool Process::assert_signalled(bool expected)
{
    if (!finished)
        perform_wait();
    return signalled == expected;
}

bool Process::assert_signal(int expected)
{
    if (!finished)
        perform_wait();
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
        throw 1;
    }
}

void Process::send_kill()
{
    if (!finished) {
        send_signal(SIGKILL);
        perform_wait();
    }
}

/* Private */
void Process::setup_parent()
{
    // Close the ends of the pipes that are being used in the child.
    if (close(fdIn[READ]) == -1 || close(fdOut[WRITE]) == -1 ||
            close(fdErr[WRITE]) == -1 || close(fdCheck[WRITE]) == -1) {
        throw 1;
    }

    // Attempt to read on check pipe. If data is available, then exec failed.
    char buf[5];
    if (read(fdCheck[READ], buf, 5) != 0) {
        perform_wait();
        throw 1;
    }

    // Close the check pipe, now we are finished with it.
    if (close(fdCheck[READ]) == -1)
        throw 1;

    // Open the remaining pipes as files, for ease of use.
    input = fdopen(fdIn[WRITE], "w"); // Input from parent to child.
    output = fdopen(fdOut[READ], "r"); // stdout from child to parent.
    error = fdopen(fdErr[READ], "r"); // stderr from child to parent.

    if (input == NULL || output == NULL || error == NULL) {
        throw 1;
    }
}

void Process::setup_child(std::vector<std::string> argv)
{
    bool do_exec = true;

    // Set up child input (stdin)
    if (close(fdIn[WRITE]) == -1 ||
            dup2(fdIn[READ], STDIN_FILENO) == -1 ||
            close(fdIn[READ]) == -1) {
        do_exec = false;
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
    for (int i = 0; i < length; ++i) {
        delete [] args[i];
    }
    delete [] args;
}

bool Process::expect_file(char *filePath, FILE *stream)
{
    std::ifstream expectedOutput (filePath);

    if (!expectedOutput.is_open()) {
        // TODO: Raise error - error opening file
        throw 1;
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

    while (!feof(stream)) {
        if (fgets(buf, 80, stream) == NULL)
            break;
        std::cout << buf;
    }

    delete [] buf;
}

void Process::perform_wait()
{
    if (!finished) {
        // Wait on the child and reap it once it is complete
        int status;
        waitpid(childPid, &status, 0);

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
        if (input != NULL)
            fclose(input);

        if (output != NULL)
            fclose(output);

        if (error != NULL)
            fclose(output);

        finished = true;
    }
}
