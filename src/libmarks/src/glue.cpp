#include <Python.h>
#include <boost/python.hpp>
#include <boost/python/stl_iterator.hpp>
#include <vector>
#include <string>
#include <sstream>
#include <boost/shared_ptr.hpp>

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
    std::ostringstream oss;
    oss << "MARKS: Call to fork() failed";
    if (!e.message.empty()) {
        oss << " [" << e.message << ']';
    }
    PyErr_SetString(PyExc_RuntimeError, oss.str().c_str());
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

void stream_finished_exception_translator(const StreamFinishedException& e) {
    PyErr_SetString(PyExc_RuntimeError, "MARKS: Tried to read stream after child finished");
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
    register_exception_translator<StreamFinishedException>(&stream_finished_exception_translator);

    /* Allow LD_PRELOAD value to be set for all processes */
    def("set_ld_preload", set_ld_preload);
    def("get_ld_preload", get_ld_preload);

    class_<Process, boost::shared_ptr<Process> >("Process", "Process class docstring", no_init)
        .def("__init__", make_constructor(&create_process, default_call_policies(), (arg("argv"), arg("input_file")="")))
        .add_property("pid", &Process::get_pid)
        .add_property("exit_status", &Process::get_exit_status)
        .add_property("abnormal_exit", &Process::get_abnormal_exit)
        .add_property("signalled", &Process::get_signalled)
        .add_property("signal", &Process::get_signal)
        .def("timeout", &Process::get_timeout)
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
        .def("send_signal_group", &Process::send_signal_group)
        .def("kill", &Process::send_kill)
        .def("check_signalled", &Process::check_signalled)
    ;

    class_<TimeoutProcess, boost::shared_ptr<TimeoutProcess>, bases<Process> >("TimeoutProcess", "Timeout Process class docstring", no_init)
        .def("__init__", make_constructor(&create_timeout_process, default_call_policies(), (arg("argv"), arg("timeout"), arg("input_file")="")))
        .add_property("pid", &TimeoutProcess::get_pid)
        .add_property("exit_status", &TimeoutProcess::get_exit_status)
        .add_property("abnormal_exit", &TimeoutProcess::get_abnormal_exit)
        .add_property("signalled", &TimeoutProcess::get_signalled)
        .add_property("signal", &TimeoutProcess::get_signal)
        .def("timeout", &TimeoutProcess::get_timeout)
        .def("send", &TimeoutProcess::send)
        .def("send_file", &TimeoutProcess::send_file)
        .def("finish_input", &TimeoutProcess::finish_input)
        .def("expect_stdout", &TimeoutProcess::expect_stdout)
        .def("expect_stderr", &TimeoutProcess::expect_stderr)
        .def("expect_stdout_file", &TimeoutProcess::expect_stdout_file)
        .def("expect_stderr_file", &TimeoutProcess::expect_stderr_file)
        .def("readline_stdout", &TimeoutProcess::readline_stdout)
        .def("readline_stderr", &TimeoutProcess::readline_stderr)
        .def("print_stdout", &TimeoutProcess::print_stdout)
        .def("print_stderr", &TimeoutProcess::print_stderr)
        .def("assert_exit_status", &TimeoutProcess::assert_exit_status)
        .def("assert_signalled", &TimeoutProcess::assert_signalled)
        .def("assert_signal", &TimeoutProcess::assert_signal)
        .def("send_signal", &TimeoutProcess::send_signal)
        .def("send_signal_group", &TimeoutProcess::send_signal_group)
        .def("kill", &TimeoutProcess::send_kill)
        .def("check_signalled", &TimeoutProcess::check_signalled)
    ;

    class_<TracedProcess, boost::shared_ptr<TracedProcess>, bases<Process> >("TracedProcess", "Traced Process class docstring", no_init)
        .def("__init__", make_constructor(&create_traced_process, default_call_policies(), (arg("argv"), arg("timeout"), arg("input_file")="")))
        .add_property("pid", &TracedProcess::get_pid)
        .add_property("exit_status", &TracedProcess::get_exit_status)
        .add_property("abnormal_exit", &TracedProcess::get_abnormal_exit)
        .add_property("signalled", &TracedProcess::get_signalled)
        .add_property("signal", &TracedProcess::get_signal)
        .def("timeout", &TracedProcess::get_timeout)
        .def("send", &TracedProcess::send)
        .def("send_file", &TracedProcess::send_file)
        .def("finish_input", &TracedProcess::finish_input)
        .def("expect_stdout", &TracedProcess::expect_stdout)
        .def("expect_stderr", &TracedProcess::expect_stderr)
        .def("expect_stdout_file", &TracedProcess::expect_stdout_file)
        .def("expect_stderr_file", &TracedProcess::expect_stderr_file)
        .def("readline_stdout", &TracedProcess::readline_stdout)
        .def("readline_stderr", &TracedProcess::readline_stderr)
        .def("print_stdout", &TracedProcess::print_stdout)
        .def("print_stderr", &TracedProcess::print_stderr)
        .def("assert_exit_status", &TracedProcess::assert_exit_status)
        .def("assert_signalled", &TracedProcess::assert_signalled)
        .def("assert_signal", &TracedProcess::assert_signal)
        .def("send_signal", &TracedProcess::send_signal)
        .def("send_signal_group", &TracedProcess::send_signal_group)
        .def("kill", &TracedProcess::send_kill)
        .def("check_signalled", &TracedProcess::check_signalled)
        .def("child_pids", &TracedProcess::child_pids_list)
    ;

}
