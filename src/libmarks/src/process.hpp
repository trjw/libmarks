#include <string>
#include <vector>
#include <cstdio>
#include <sys/wait.h>


/* File descriptor ends for pipes */
#define READ 0
#define WRITE 1

class Process {
    int fdIn[2], fdOut[2], fdErr[2], fdCheck[2];
    pid_t childPid;
    FILE *input, *output, *error;
    bool finished;
    int exitStatus, signalNum;
    bool abnormalExit, signalled;

    void init(std::vector<std::string>, std::string);
    void init(std::vector<std::string>);
    void setup_parent(bool);
    void setup_child(std::vector<std::string>, std::string);
    char **create_args(std::vector<std::string>);
    void delete_args(char **, size_t);
    bool expect(const std::string&, FILE *);
    bool expect_file(char *, FILE *);
    std::string readline(FILE *);
    void print_stream(FILE *);
    void perform_wait();

public:
    Process(std::vector<std::string>);
    Process(std::vector<std::string>, std::string);
    ~Process();
    bool send(const std::string&);
    bool send_file(char *);
    bool finish_input();
    bool expect_stdout(const std::string&);
    bool expect_stderr(const std::string&);
    bool expect_stdout_file(char *);
    bool expect_stderr_file(char *);
    std::string readline_stdout();
    std::string readline_stderr();
    void print_stdout();
    void print_stderr();
    bool assert_exit_status(int);
    bool assert_signalled(bool);
    bool assert_signal(int);
    int get_exit_status();
    bool get_abnormal_exit();
    bool get_signalled();
    int get_signal();
    void send_signal(int);
    void send_kill();
};
