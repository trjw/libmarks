#include <Python.h>
#include <boost/python.hpp>
#include <boost/python/stl_iterator.hpp>
#include <vector>
#include <string>

#include "process.hpp"


/*
 * Iterable converter taken from http://stackoverflow.com/a/15940413
 */

/// @brief Type that allows for registration of conversions from
///        python iterable types.
struct iterable_converter
{
  /// @note Registers converter from a python interable type to the
  ///       provided type.
  template <typename Container>
  iterable_converter&
  from_python()
  {
    boost::python::converter::registry::push_back(
      &iterable_converter::convertible,
      &iterable_converter::construct<Container>,
      boost::python::type_id<Container>());
    return *this;
  }

  /// @brief Check if PyObject is iterable.
  static void* convertible(PyObject* object)
  {
    return PyObject_GetIter(object) ? object : NULL;
  }

  /// @brief Convert iterable PyObject to C++ container type.
  ///
  /// Container Concept requirements:
  ///
  ///   * Container::value_type is CopyConstructable.
  ///   * Container can be constructed and populated with two iterators.
  ///     I.e. Container(begin, end)
  template <typename Container>
  static void construct(
    PyObject* object,
    boost::python::converter::rvalue_from_python_stage1_data* data)
  {
    namespace python = boost::python;
    // Object is a borrowed reference, so create a handle indicting it is
    // borrowed for proper reference counting.
    python::handle<> handle(python::borrowed(object));

    // Obtain a handle to the memory block that the converter has allocated
    // for the C++ type.
    typedef python::converter::rvalue_from_python_storage<Container>
                                                                 storage_type;
    void* storage = reinterpret_cast<storage_type*>(data)->storage.bytes;

    typedef python::stl_input_iterator<typename Container::value_type>
                                                                     iterator;

    // Allocate the C++ type into the converter's memory block, and assign
    // its handle to the converter's convertible variable.  The C++
    // container is populated by passing the begin and end iterators of
    // the python object to the container's constructor.
    data->convertible = new (storage) Container(
      iterator(python::object(handle)), // begin
      iterator());                      // end
  }
};

/* Exception translation */
void close_exception_translator(const CloseException& e) {
    PyErr_SetString(PyExc_RuntimeError, "MARKS: Call to close() failed");
}

void exec_exception_translator(const ExecException& e) {
    PyErr_SetString(PyExc_RuntimeError, "MARKS: Call to exec() failed");
}

void fdopen_exception_translator(const FdOpenException& e) {
    PyErr_SetString(PyExc_RuntimeError, "MARKS: Call to fdopen() failed");
}

void fork_exception_translator(const ForkException& e) {
    PyErr_SetString(PyExc_RuntimeError, "MARKS: Call to fork() failed");
}

void pipe_exception_translator(const PipeException& e) {
    PyErr_SetString(PyExc_RuntimeError, "MARKS: Call to pipe() failed");
}

void signal_exception_translator(const SignalException& e) {
    PyErr_SetString(PyExc_RuntimeError, "MARKS: Could not send signal to process");
}

void stream_exception_translator(const StreamException& e) {
    PyErr_SetString(PyExc_RuntimeError, "MARKS: Unexpected error with stream");
}


BOOST_PYTHON_MODULE(process)
{
    using namespace boost::python;

    // Register interable conversions.
    iterable_converter()
        // Build-in type.
        .from_python<std::vector<std::string> >();

    register_exception_translator<CloseException>(&close_exception_translator);
    register_exception_translator<ExecException>(&exec_exception_translator);
    register_exception_translator<FdOpenException>(&fdopen_exception_translator);
    register_exception_translator<ForkException>(&fork_exception_translator);
    register_exception_translator<PipeException>(&pipe_exception_translator);
    register_exception_translator<SignalException>(&signal_exception_translator);
    register_exception_translator<StreamException>(&stream_exception_translator);

    class_<Process>("Process", "Process class docstring", init<std::vector<std::string> >(args("argv")))
        .def(init<std::vector<std::string>, std::string>(args("argv", "input_file")))
        .add_property("exit_status", &Process::get_exit_status)
        .add_property("abnormal_exit", &Process::get_abnormal_exit)
        .add_property("signalled", &Process::get_signalled)
        .add_property("signal", &Process::get_signal)
        .def("send", &Process::send)
        .def("send_file", &Process::send_file)
        .def("finish_input", &Process::finish_input)
        .def("expect_stdout", &Process::expect_stdout)
        .def("expect_stderr", &Process::expect_stderr)
        .def("expect_stdout_file", &Process::expect_stdout_file)
        .def("expect_stderr_file", &Process::expect_stderr_file)
        .def("readline_stdout", &Process::readline_stdout)
        .def("readline_stderr", &Process::readline_stderr)
        .def("print_stdout", &Process::print_stdout)
        .def("print_stderr", &Process::print_stderr)
        .def("assert_exit_status", &Process::assert_exit_status)
        .def("assert_signalled", &Process::assert_signalled)
        .def("assert_signal", &Process::assert_signal)
        .def("send_signal", &Process::send_signal)
        .def("kill", &Process::send_kill)
    ;

}
