.DEFAULT_GOAL:= all
.PHONY: all clean install

# Disable warnings from boost compilation
BOOSTISMS = -Wno-c++11-extra-semi -Wno-c++11-long-long -Wno-c11-extensions -DBOOST_BIND_GLOBAL_PLACEHOLDERS
CC=clang++
CFLAGS=-Wall -Werror -pedantic $(BOOSTISMS)

# Python related compilation flags
PYTHON_INCLUDES = -I$(PYTHON_INCLUDE)
PYTHON_LDFLAGS = -L$(PYTHON_LIB)/config -l$(PYTHON_LIBNAME)

# Build related variables
TEMP_BUILD_DEST=../marks
PROCESS_PARTIALS = src/glue.o src/process.o src/tracedProcess.o
TARGETS = $(PROCESS_PARTIALS) src/process.so src/libprotect.so

debug: CFLAGS += -g -DDEBUG
debug: clean all

all: $(TARGETS) src/process.so
	@# Create destination directory
	mkdir -p $(TEMP_BUILD_DEST)
	@# Copy the compiled library
	cp src/process.so $(TEMP_BUILD_DEST)/process.so
	cp src/libprotect.so $(TEMP_BUILD_DEST)/libprotect.so
	@# Compile and copy the Python module
	python3 compile_py.py py_src $(TEMP_BUILD_DEST)

src/process.so: $(PROCESS_PARTIALS)
	$(CC) $(CFLAGS) -shared -Wl,--export-dynamic $(PROCESS_PARTIALS) -L$(BOOST_LIB) -l$(BOOST_LIBNAME) $(PYTHON_LDFLAGS) -o $@

src/glue.o: src/glue.cpp src/process.hpp
	$(CC) $(CFLAGS) $(PYTHON_INCLUDES) -I$(BOOST_INC) -fPIC -pthread -c $< -o $@

src/process.o: src/process.cpp src/process.hpp
	$(CC) $(CFLAGS) $(PYTHON_INCLUDES) -I$(BOOST_INC) -fPIC -pthread -c $< -o $@

src/tracedProcess.o: src/traced_process.cpp src/process.hpp
	$(CC) $(CFLAGS) $(PYTHON_INCLUDES) -I$(BOOST_INC) -fPIC -pthread -c $< -o $@

src/libprotect.so: src/protection.c
	gcc -std=gnu99 $(CFLAGS) -ldl -shared -Wl,--export-dynamic -fPIC $< -o $@

install: all 
	install -m u=rw,g=r,o=r $(TEMP_BUILD_DEST)/*.pyc $(INSTALL_DEST)
	install -m u=rw,g=r,o=r $(TEMP_BUILD_DEST)/*.so $(INSTALL_DEST) 

clean:
	rm -f $(TARGETS)
	rm -rf $(TEMP_BUILD_DEST)