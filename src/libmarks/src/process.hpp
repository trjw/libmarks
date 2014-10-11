#include <string>
#include <vector>
#include <cstdio>
#include <set>
#include <sys/wait.h>
#include <pthread.h>
#include <boost/shared_ptr.hpp>
#include <boost/python.hpp>

/* File descriptor ends for pipes */
#define READ 0
#define WRITE 1

/* Signals */
#define SIG_CHECK 0

/* Maximum allowed child processes */
#define MAX_CHILD_COUNT 20

/* Debug printing */
#ifdef DEBUG
#define D(x) do { std::cerr << x; } while (0)
#else
#define D(x) do {} while (0)
#endif

/* Allow global value for LD_PRELOAD to be set for all Processes created */
void set_ld_preload(std::string);
std::string get_ld_preload();

class Process {
protected:
    std::vector<std::string> argv;
    std::string inputFile;
    int fdIn[2], fdOut[2], fdErr[2], fdCheck[2];
    pid_t childPid;
    FILE *input, *output, *error;
    bool finished;
    int exitStatus, signalNum;
    bool abnormalExit, signalled;
    bool timeout;
    pthread_mutex_t finishMutex;

    void setup_parent();
    virtual int setup_parent_pre_exec();
    void setup_child();
    virtual int setup_child_additional();
    char **create_args(std::vector<std::string> &);
    void delete_args(char **, size_t);
    bool expect(const std::string&, FILE **);
    bool expect_file(char *, FILE **);
    std::string readline(FILE **);
    void print_stream(FILE **);
    bool close_stream(FILE **);
    void finish_process(int);
    void perform_wait(bool);

public:
    Process(std::vector<std::string>);
    Process(std::vector<std::string>, std::string);
    ~Process();
    virtual void init();
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
protected:
    int timeout_duration;
    pthread_t timeoutThread;
    bool timeoutStarted;
    void init_timeout();
    virtual void perform_timeout();
    static void *timeout_thread(void *);

public:
    TimeoutProcess(std::vector<std::string>, int);
    TimeoutProcess(std::vector<std::string>, int, std::string);
    ~TimeoutProcess();
    virtual void init();
    int get_timeout_duration();
    void timeout_process();
};

/* Tracing */
class TracedProcess: public TimeoutProcess {
private:
    pthread_t tracerThread;
    bool traceStarted;
    std::set<pid_t> children;
    int setup_parent_pre_exec();
    int setup_child_additional();
    void perform_timeout();
    void init_tracer();
    void trace_child();
    int trace_new_child(pid_t);
    void trace_syscall(pid_t);
    void kill_threads(std::set<pid_t> &);
    static void *trace_thread(void *);

public:
    TracedProcess(std::vector<std::string>, int);
    TracedProcess(std::vector<std::string>, int, std::string);
    ~TracedProcess();
    virtual void init();
    std::set<pid_t> child_pids();
    boost::python::list child_pids_list();
};

/* Factories */
boost::shared_ptr<Process> create_process(std::vector<std::string> argv, std::string inputFile);
boost::shared_ptr<TimeoutProcess> create_timeout_process(std::vector<std::string> argv, int timeout, std::string inputFile="");
boost::shared_ptr<TracedProcess> create_traced_process(std::vector<std::string> argv, int timeout, std::string inputFile="");

/* Exceptions */
struct CloseException {};
struct ExecException {};
struct FdOpenException {};
struct ForkException {};
struct PipeException {};
struct SignalException {};
struct StreamException {};
struct StreamFinishedException {};
