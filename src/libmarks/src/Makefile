CC = clang++

# location of the Python header files

PYTHON_VERSION = 2.7
# PYTHON_INCLUDE = /usr/include/python$(PYTHON_VERSION)
# PYTHON_LIB = /usr/lib/python$(PYTHON_VERSION)
PYTHON_INCLUDE = /usr/local/Cellar/python/2.7.6_1/Frameworks/Python.framework/Versions/2.7/include/python$(PYTHON_VERSION)
PYTHON_LIB = /usr/local/Cellar/python/2.7.6_1/Frameworks/Python.framework/Versions/2.7/lib/python$(PYTHON_VERSION)

# location of the Boost Python include files and library

BOOST_INC = /usr/local/include
BOOST_LIB = /usr/local/lib

# compile mesh classes
TARGET = glue
TARGETS = glue.o process.o

DESTINATION = ../../marks

.DEFAULT=all
.PHONY=all clean


all: $(TARGETS) process.so

clean:
	rm $(TARGETS) process.so

process.so: $(TARGETS)
	$(CC) -dynamiclib $(TARGETS) -L$(BOOST_LIB) -lboost_python -L$(PYTHON_LIB)/config -lpython$(PYTHON_VERSION) -o process.so
	cp process.so $(DESTINATION)/process.so

#	$(CC) -shared -Wl,--export-dynamic $(TARGET).o -L$(BOOST_LIB) -lboost_python-$(PYTHON_VERSION) -L$(PYTHON_LIB)/config -lpython$(PYTHON_VERSION) -o $(DESTINATION)/$(TARGET).so

# $(TARGET).o: $(TARGET).cpp
# 	$(CC) -stdlib=libstdc++ -I$(PYTHON_INCLUDE) -I$(BOOST_INC) -fPIC -c $(TARGET).cpp

glue.o: glue.cpp process.hpp
	$(CC) -I$(PYTHON_INCLUDE) -I$(BOOST_INC) -fPIC -c glue.cpp

process.o: process.cpp process.hpp
	$(CC) -I$(PYTHON_INCLUDE) -I$(BOOST_INC) -fPIC -c process.cpp
