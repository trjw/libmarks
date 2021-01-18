CC=gcc
CFLAGS=-Wall -pedantic -std=gnu99

.PHONY: all clean
.DEFAULT_GOAL:=all

all: retcode

retcode: retcode.o
	$(CC) $(CFLAGS) retcode.o -o retcode

clean:
	rm -f *.o
	rm -f retcode