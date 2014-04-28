#include <Python.h>
#include <boost/python.hpp>
#include <vector>
#include <string>

#include "process.hpp"

using namespace boost::python;


int hw()
{
    return 17;
}

char const* greet()
{
   return "hello, world";
}

BOOST_PYTHON_MODULE(process)
{
    using namespace boost::python;
    def("greet", greet);
    // def("hi", hw);

    class_<Process>("Process", "Process class docstring", init<>());
    //     .def("send", &Process::send)
    //     .def("send_file", &Process::send_file)
    //     .def("expect_stdout", &Process::expect_stdout)
    //     .def("expect_stderr", &Process::expect_stderr)
    //     .def("expect_stdout_file", &Process::expect_stdout_file)
    //     .def("expect_stderr_file", &Process::expect_stderr_file)
    //     .def("assert_exit_status", &Process::assert_exit_status)
    //     .def("assert_signalled", &Process::assert_signalled)
    //     .def("assert_signal", &Process::assert_signal)
    //     .def("kill", &Process::send_kill)
    // ;

}
