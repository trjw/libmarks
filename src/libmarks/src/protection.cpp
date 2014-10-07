#define _GNU_SOURCE

#include <stdio.h>
#include <unistd.h>
#include <sys/types.h>
#include <signal.h>
#include <errno.h>
#include <dlfcn.h>

/* Ugly hack to supress warning about void* to fn pointer */
union orig_kill_function {
    void *sym;
    int (*fn)(pid_t, int);
};

/**
 * Safer version of kill.
 * Do not allow all processes to be signalled (pid == -1).
 */
int kill(pid_t pid, int sig)
{
    if (pid == -1) {
        /* Do not allow all processes to be terminated. */
        // errno = EPERM;
        // return -1;
        /* Kill the process group instead. */
        pid = -getpgrp();
    }

    union orig_kill_function orig_kill;
    orig_kill.sym = dlsym(RTLD_NEXT, "kill");
    return (*orig_kill.fn)(pid, sig);
}
