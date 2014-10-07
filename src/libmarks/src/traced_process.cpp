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

#ifdef __linux__
#include <sys/ptrace.h>
#include <sys/reg.h>
#endif

#include "process.hpp"

/** Traced Process **/
/* Public */
TracedProcess::TracedProcess(std::vector<std::string> argv, int timeout, std::string inputFile):
    TimeoutProcess(argv, timeout, inputFile)
{
    init_tracer();
}

TracedProcess::TracedProcess(std::vector<std::string> argv, int timeout):
    TimeoutProcess(argv, timeout, "")
{
    init_tracer();
}

TracedProcess::~TracedProcess()
{
    if (!finished) {
        // Kill the Process.
        send_kill();
    }

    // Finish the timeout thread.
    pthread_cancel(timeoutThread);
    pthread_join(timeoutThread, NULL);

    // Finish the tracer thread.
    if (tracerThread != NULL) {
        pthread_cancel(tracerThread);
        pthread_join(tracerThread, NULL);
    }

    // Destroy wait mutex.
    pthread_mutex_destroy(&waitMutex);
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

/* Private */
void TracedProcess::init_tracer()
{
    tracerThread = NULL;
#ifdef __linux__
    // Create thread to perform timeout
    if (pthread_create(&tracerThread, NULL, trace_thread,
            (void *) this) != 0) {
        // Error
    }
#endif /* linux */
}

/* Tracer is linux specific, so only compile if on a linux machine. */

void kill_threads(std::set<pid_t> &threads)
{
    std::set<pid_t>::iterator it;
    for (it = threads.begin(); it != threads.end(); ++it) {
        kill(*it, SIGKILL);
    }
}

#ifdef __linux__
void *trace_thread(void *arg)
{
    TracedProcess *tp = (TracedProcess *) arg;
    pid_t child = tp->childPid;

    // Obtain mutex.
    pthread_mutex_lock(&(tp->waitMutex));

    // Status information from the process that was waited upon.
    int status;

    // Track all of the children created
    std::set<pid_t> &allThreads = tp->children;

    // Options to set on the traced process.
    // Schedule child to stop on next clone, fork or vfork.
    long opt = PTRACE_O_TRACECLONE | PTRACE_O_TRACEFORK | PTRACE_O_TRACEVFORK;
    // Set flag for system calls in signal number.
    opt |= PTRACE_O_TRACESYSGOOD;

    // Perform the initial wait on the child we just started.
    if (waitpid(child, &status, 0) == -1) {
        D("Unable to wait on child: " << strerror(errno) << std::endl);
    }
    // Set the options on the child process
    ptrace(PTRACE_SETOPTIONS, child, 0, opt);
    // Continue the process, stopping at the next syscall.
    ptrace(PTRACE_SYSCALL, child, 0, 0);

    D("Tracee " << child << " started and options set" << std::endl);

    while (1) {
        pid_t pid = waitpid(-1, &status, __WALL);
        D("wait happened: " << pid << " (" << status << ")" << std::endl);

        if (pid < 0) {
            if (errno == EINTR) {
                continue;
            }

            // Kill process group, because something went wrong.
            D("Failed to wait: " << strerror(errno) << std::endl);
            kill(-child, SIGKILL);
            kill_threads(allThreads);
            break;
        }

        if (WIFEXITED(status)) {
            D("\tChild process " << pid <<
                " exited with status " << WEXITSTATUS(status) << std::endl);

            if (pid == child) {
                // Main child has finished, so run final tests.
                finish_process(status);
            } else if (allThreads.erase(pid) != 1) {
                D("Could not erase child " << pid << std::endl);
            }

            if (allThreads.size() == 0 && tp->finished)
                break;

            continue;
        }

        if (WIFSIGNALED(status)) {
            D("\tChild process " << pid <<
                " killed by signal " << WTERMSIG(status) << std::endl);

            if (pid == child) {
                // Main child has finished, so run final tests.
                finish_process(status);
            } else if (allThreads.erase(pid) != 1) {
                D("Could not erase child " << pid << std::endl);
            }

            if (allThreads.size() == 0 && tp->finished)
                break;

            continue;
        }

        if (WIFSTOPPED(status)) {
            D("\tChild process " << pid << "stopped" << std::endl);
            switch (WSTOPSIG(status)) {
                case SIGSTOP:
                    D("\tsigstop" << std::endl);
                    break;
                case SIGTRAP | 0x80:
                    D("\tsigtrap from syscall" << std::endl);
                    trace_syscall(pid);
                    break;
                case SIGTRAP:
                    D("\tnormal sigtrap" << std::endl);
                    if(((status >> 16) & 0xffff) == PTRACE_EVENT_FORK) {
                        if (!trace_child(child, pid, allThreads))
                            continue;
                    }
                    break;
            }
        }

        ptrace(PTRACE_CONT, pid, 0L, 0L);
    }

    // Attempt to kill everything before exiting, in case something escaped.
    D("Final cleanup - kill process group " << child << std::endl);
    if (kill(-child, SIGKILL) == -1) {
        D("Final cleanup of process group failed: " <<
            strerror(errno) << std::endl);
    }
    kill_threads(allThreads);

    // Release mutex.
    pthread_mutex_unlock(&(tp->waitMutex));

    return NULL;
}

int trace_child(pid_t root, pid_t pid, std::set<pid_t> &threads) {
    long msg = 0;
    pid_t new_child;
    if(ptrace(PTRACE_GETEVENTMSG, pid, 0, (long) &msg) != -1) {
        new_child = msg;
        threads.insert(new_child);
        D("\tChild [" << threads.size() << "] " <<
            new_child << " created" << std::endl);

        // Check if the process limit has been reached.
        if (threads.size() >= MAX_CHILD_COUNT) {
            // Protect against forkbombs.
            // Kill all of the threads we know about.
            D("KILLING EVERYTHING " << threads.size() << std::endl);
            kill(-root, SIGKILL);
            kill_threads(threads);
            return 0;
        }

        // Tell the new process to continue.
        ptrace(PTRACE_CONT, new_child, 0, 0);
    } else {
        D("\tFailed to get PID of new child" << std::endl);
    }
    return 1;
}

void trace_syscall(pid_t pid) {
    long syscall = 0;
    syscall = ptrace(PTRACE_PEEKUSER, pid, sizeof(long) * ORIG_RAX);
    D("\tsyscall(" << syscall << ")" << std::endl);
}
#endif /* linux */
