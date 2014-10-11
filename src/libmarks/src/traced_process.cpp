#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <set>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <csignal>
#include <cerrno>
#include <unistd.h>
#include <sys/wait.h>
#include <fcntl.h>
#include <pthread.h>
#include <sys/types.h>
#include <boost/python.hpp>

#ifdef __linux__
#include <sys/ptrace.h>
#include <sys/reg.h>
#include <sys/prctl.h>
#endif

#include "process.hpp"

/** Traced Process **/

/* Use to create a new Process, so init() is called */
boost::shared_ptr<TracedProcess> create_traced_process(std::vector<std::string> argv, int timeout, std::string inputFile)
{
    boost::shared_ptr<TracedProcess> p(new TracedProcess(argv, timeout, inputFile));
    p->init();
    return p;
}

/* Public */
TracedProcess::TracedProcess(std::vector<std::string> argv, int timeout, std::string inputFile):
    TimeoutProcess(argv, timeout, inputFile), traceStarted(false)
{
}

TracedProcess::TracedProcess(std::vector<std::string> argv, int timeout):
    TimeoutProcess(argv, timeout, ""), traceStarted(false)
{
}

TracedProcess::~TracedProcess()
{
    // Finish the timeout thread.
    if (timeoutStarted) {
        pthread_cancel(timeoutThread);
        pthread_join(timeoutThread, NULL);
    }

    // Finish the tracer thread.
    if (traceStarted) {
        pthread_cancel(tracerThread);
        pthread_join(tracerThread, NULL);
    }

    if (!finished) {
        // Kill the Process.
        send_kill();
    }

    // Destroy wait mutex.
    pthread_mutex_destroy(&waitMutex);
}

void TracedProcess::init()
{
    // Do not use TimeoutProcess::init(), as it will start the timeout
    // too early for the tracing. Instead, manually init() the process
    // and then initialise the timeout after tracing has started.
    Process::init();
    init_timeout();
}

int TracedProcess::setup_parent_pre_exec()
{
    // Start the tracer to ensure the child can continue then exec()
    init_tracer();
    return 1;
}

int TracedProcess::setup_child_additional()
{
    std::cerr << "TRACE PROCESS EXECUTE STUFF" << std::endl;
#ifdef __linux__ /* Trace is linux specific */
    // Mark the child to be traced.
    if (kill(getpid(), SIGSTOP) == -1)
        return -1;
#endif /* linux */
    return 1;
}

void TracedProcess::perform_timeout()
{
    if (!finished) {
        timeout = true;
        kill_threads(children);
        send_kill();
    }
}

std::set<pid_t> TracedProcess::child_pids()
{
    return children;
}

boost::python::list TracedProcess::child_pids_list()
{
    boost::python::list l;
    std::set<pid_t>::const_iterator it;
    for (it = children.begin(); it != children.end(); ++it)
        l.append(*it);
    return l;
}

/* Private */
void TracedProcess::init_tracer()
{
#ifdef __linux__ /* Trace is linux specific */
    // Create thread to perform timeout
    if (pthread_create(&tracerThread, NULL, &TracedProcess::trace_thread,
            (void *) this) != 0) {
        // Error
        return;
    }
    traceStarted = true;
#endif /* linux */
}

void TracedProcess::trace_child()
{
    // Obtain mutex, as we are using wait().
    pthread_mutex_lock(&waitMutex);

#ifdef __linux__ /* Trace is linux specific */
    // Status information from the process that was waited upon.
    int status;
    bool optionsSet = false; // Flag for child options being set.

    // Options to set on the traced process.
    // Schedule child to stop on next clone, fork or vfork.
    long opt = PTRACE_O_TRACECLONE | PTRACE_O_TRACEFORK | PTRACE_O_TRACEVFORK;
    // Set flag for system calls in signal number.
    opt |= PTRACE_O_TRACESYSGOOD;

    // Attach to the child so we can start tracing it.
    if (ptrace(PTRACE_ATTACH, childPid, 0, 0) == -1) {
        D("Failed to attach to child" << std::endl);
    }

    D("Time to start tracing the child " << childPid << std::endl);

    while (1) {
        pid_t pid = waitpid(-1, &status, __WALL);
        D("Wait happened: " << pid << " (" << status << ")" << std::endl);

        if (pid < 0) {
            if (errno == EINTR) {
                continue;
            }

            // Kill process group, because something went wrong.
            D("Failed to wait: " << strerror(errno) << std::endl);
            kill(-childPid, SIGKILL);
            kill_threads(children);
            break;
        }

        if (WIFEXITED(status)) {
            D("\tChild process " << pid <<
                " exited with status " << WEXITSTATUS(status) << std::endl);

            if (pid == childPid) {
                // Main child has finished, so run final tests.
                finish_process(status);
            } else if (children.erase(pid) != 1) {
                D("\tCould not erase child " << pid << std::endl);
            }

            if (children.size() == 0 && finished)
                break;

            continue;
        }

        if (WIFSIGNALED(status)) {
            D("\tChild process " << pid <<
                " killed by signal " << WTERMSIG(status) << std::endl);

            if (pid == childPid) {
                // Main child has finished, so run final tests.
                finish_process(status);
            } else if (children.erase(pid) != 1) {
                D("Could not erase child " << pid << std::endl);
            }

            if (children.size() == 0 && finished)
                break;

            continue;
        }

        if (WIFSTOPPED(status)) {
            D("\tChild process " << pid << " stopped" << std::endl);
            switch (WSTOPSIG(status)) {
                case SIGSTOP:
                    D("\tsigstop" << std::endl);
                    if (pid == childPid && !optionsSet) {
                        // Set the options on the child process
                        ptrace(PTRACE_SETOPTIONS, pid, 0, opt);
                        // Continue the process, stopping at the next syscall.
                        ptrace(PTRACE_SYSCALL, pid, 0, 0);
                        optionsSet = true;
                        D("\tTracee " << pid << " had options set" << std::endl);
                        continue;
                    }
                    break;
                case SIGTRAP | 0x80:
                    D("\tsigtrap from syscall" << std::endl);
                    trace_syscall(pid);
                    break;
                case SIGTRAP:
                    D("\tnormal sigtrap" << std::endl);
                    if(((status >> 16) & 0xffff) == PTRACE_EVENT_FORK) {
                        if (!trace_new_child(pid))
                            continue;
                    }
                    break;
            }
        }

        ptrace(PTRACE_CONT, pid, 0L, 0L);
    }

    // Attempt to kill everything before exiting, in case something escaped.
    D("Final cleanup - kill process group " << childPid << std::endl);
    if (kill(-childPid, SIGKILL) == -1) {
        D("Final cleanup of process group failed: " <<
            strerror(errno) << std::endl);
    }
    kill_threads(children);
#endif /* linux */

    // Release mutex.
    pthread_mutex_unlock(&waitMutex);
}

int TracedProcess::trace_new_child(pid_t pid)
{
#ifdef __linux__ /* Trace is linux specific */
    long msg = 0;
    pid_t newChild;
    if(ptrace(PTRACE_GETEVENTMSG, pid, 0, (long) &msg) != -1) {
        newChild = msg;
        children.insert(newChild);
        D("\tChild [" << children.size() << "] " <<
            newChild << " created" << std::endl);

        // Check if the process limit has been reached.
        if (children.size() >= MAX_CHILD_COUNT) {
            // Protect against forkbombs.
            // Kill all of the threads we know about.
            D("KILLING EVERYTHING " << children.size() << std::endl);
            kill(-childPid, SIGKILL);
            kill_threads(children);
            return 0;
        }

        // Tell the new process to continue.
        ptrace(PTRACE_CONT, newChild, 0, 0);
    } else {
        D("\tFailed to get PID of new child" << std::endl);
    }
#endif /* linux */
    return 1;
}

void TracedProcess::trace_syscall(pid_t pid)
{
#ifdef __linux__ /* Trace is linux specific */
    //long syscall = 0;
    //syscall = ptrace(PTRACE_PEEKUSER, pid, sizeof(long) * ORIG_RAX);
    //D("\tsyscall(" << syscall << ")" << std::endl);
#endif /* linux */
}

void TracedProcess::kill_threads(std::set<pid_t> &threads)
{
    std::set<pid_t>::iterator it;
    for (it = threads.begin(); it != threads.end(); ++it) {
        kill(*it, SIGKILL);
    }
}

void *TracedProcess::trace_thread(void *arg)
{
    TracedProcess *tp = (TracedProcess *) arg;

    // Trace the child process.
    tp->trace_child();

    // End thread.
    pthread_exit(NULL);
}
