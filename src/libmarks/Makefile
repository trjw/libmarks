.DEFAULT: all
.PHONY: all clean

CC = clang++
CFLAGS = -Wall -Werror -pedantic

# location of the Python header files
PYTHON_VERSION = 2.7
# PYTHON_INCLUDE = /usr/include/python$(PYTHON_VERSION)
# PYTHON_LIB = /usr/lib/python$(PYTHON_VERSION)
PYTHON_INCLUDES = $(shell python-config --includes)
PYTHON_LDFLAGS = $(shell python-config --ldflags)

# location of the Boost Python include files and library
BOOST_INC = /usr/local/include
BOOST_LIB = /usr/local/lib

TARGETS = src/glue.o src/process.o

DESTINATION = ../marks

all: $(TARGETS) src/process.so
	@# Create destination directory
	mkdir -p $(DESTINATION)
	@# Copy the compiled library
	cp src/process.so $(DESTINATION)/process.so
	@# Compile and copy the Python module
	python compile_py.py py_src $(DESTINATION)

clean:
	rm -f $(TARGETS) src/process.so
	rm -rf $(DESTINATION)

src/process.so: $(TARGETS)
	$(CC) -dynamiclib $(TARGETS) -L$(BOOST_LIB) -lboost_python $(PYTHON_LDFLAGS) -o src/process.so

# $(CC) -dynamiclib $(TARGETS) -L$(BOOST_LIB) -lboost_python -L$(PYTHON_LIB)/config -lpython$(PYTHON_VERSION) -o process.so

src/glue.o: src/glue.cpp src/process.hpp
	$(CC) $(PYTHON_INCLUDES) -I$(BOOST_INC) -fPIC -pthread -c src/glue.cpp -o src/glue.o

src/process.o: src/process.cpp src/process.hpp
	$(CC) $(CFLAGS) $(PYTHON_INCLUDES) -I$(BOOST_INC) -fPIC -pthread -c src/process.cpp -o src/process.o
