.DEFAULT=all
.PHONY=all clean

CC = clang++

# location of the Python header files
PYTHON_VERSION = 2.7
# PYTHON_INCLUDE = /usr/include/python$(PYTHON_VERSION)
# PYTHON_LIB = /usr/lib/python$(PYTHON_VERSION)
PYTHON_INCLUDES = $(shell python-config --includes)
PYTHON_LDFLAGS = $(shell python-config --ldflags)

# location of the Boost Python include files and library
BOOST_INC = /usr/local/include
BOOST_LIB = /usr/local/lib

TARGETS = glue.o process.o

DESTINATION = ../../marks

all: $(TARGETS) process.so

clean:
	rm $(TARGETS) process.so

process.so: $(TARGETS)
	$(CC) -dynamiclib $(TARGETS) -L$(BOOST_LIB) -lboost_python $(PYTHON_LDFLAGS) -o process.so
	mkdir -p $(DESTINATION)
	cp process.so $(DESTINATION)/process.so

# $(CC) -dynamiclib $(TARGETS) -L$(BOOST_LIB) -lboost_python -L$(PYTHON_LIB)/config -lpython$(PYTHON_VERSION) -o process.so

glue.o: glue.cpp process.hpp
	$(CC) $(PYTHON_INCLUDES) -I$(BOOST_INC) -fPIC -pthread -c glue.cpp

process.o: process.cpp process.hpp
	$(CC) $(PYTHON_INCLUDES) -I$(BOOST_INC) -fPIC -pthread -c process.cpp
