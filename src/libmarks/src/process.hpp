#include <string>
#include <vector>
#include <cstdio>
#include <sys/wait.h>


/* File descriptor ends for pipes */
#define READ 0
#define WRITE 1

class Process {
    int fdIn[2], fdOut[2], fdErr[2];
    pid_t childPid;
    FILE *input, *output, *error;
    bool finished;
    int exitStatus, signalNum;
    bool abnormalExit, signalled;

    void setup_parent();
    void setup_child(std::vector<std::string>);
    char **create_args(std::vector<std::string>);
    void delete_args(char **, size_t);
    bool expect(const std::string&, FILE *);
    bool expect_file(char *, FILE *);
    void print_stream(FILE *);
    void perform_wait();

public:
    Process (std::vector<std::string>);
    Process(){}
    ~Process();
    bool send(const std::string&);
    bool send_file(char *);
    bool expect_stdout(const std::string&);
    bool expect_stderr(const std::string&);
    bool expect_stdout_file(char *);
    bool expect_stderr_file(char *);
    void print_stdout();
    void print_stderr();
    bool assert_exit_status(int);
    bool assert_signalled(bool);
    bool assert_signal(int);
    void send_kill();
};
