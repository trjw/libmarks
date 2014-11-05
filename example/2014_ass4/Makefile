.DEFAULT=all
.PHONY=all clean

CC = gcc
CFLAGS = -Wall -Werror -pedantic


all: locked ass4protect.so

locked:
	touch locked
	chmod a-r locked

ass4protect.so: protect.c
	$(CC) -std=gnu99 $(CFLAGS) -ldl -dynamiclib -fPIC $< -o $@
	# $(CC) -std=gnu99 $(CFLAGS) -ldl -shared -Wl,--export-dynamic -fPIC $< -o $@
