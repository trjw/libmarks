#include <string>
#include <vector>
#include <cstdio>
#include <sys/wait.h>
#include <pthread.h>

/* File descriptor ends for pipes */
#define READ 0
#define WRITE 1

/* Signals */
#define SIG_CHECK 0

/* Debug printing */
#ifdef DEBUG
#define D(x) do { std::cerr << x; } while (0)
#else
#define D(x) do {} while (0)
#endif

class Process {
protected:
    int fdIn[2], fdOut[2], fdErr[2], fdCheck[2];
    pid_t childPid;
    FILE *input, *output, *error;
    bool finished;
    int exitStatus, signalNum;
    bool abnormalExit, signalled;
    bool timeout;
    pthread_mutex_t waitMutex;

    void init(std::vector<std::string>, std::string);
    void init(std::vector<std::string>);
    void setup_parent(bool);
    void setup_child(std::vector<std::string>, std::string);
    void execute_program(std::vector<std::string>);
    char **create_args(std::vector<std::string>);
    void delete_args(char **, size_t);
    bool expect(const std::string&, FILE *);
    bool expect_file(char *, FILE *);
    std::string readline(FILE *);
    void print_stream(FILE *);
    bool close_stream(FILE **);
    void perform_wait(bool);

public:
    Process(std::vector<std::string>);
    Process(std::vector<std::string>, std::string);
    ~Process();
    pid_t get_pid();
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
    void send_signal_group(int);
    void send_kill();
    bool check_signalled();
    bool get_timeout();
};

class TimeoutProcess: public Process {
private:
    int timeout_duration;
    pthread_t thread;
    void init_timeout();

public:
    TimeoutProcess(std::vector<std::string>, int);
    TimeoutProcess(std::vector<std::string>, int, std::string);
    ~TimeoutProcess();
    int get_timeout_duration();
    void perform_timeout();
};

/* Timeout thread */
void *timeout_thread(void *);

/* Exceptions */
struct CloseException {};
struct ExecException {};
struct FdOpenException {};
struct ForkException {};
struct PipeException {};
struct SignalException {};
struct StreamException {};
struct StreamFinishedException {};
