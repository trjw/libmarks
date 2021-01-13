# Libmarks: A Python framework for running functional tests on source code

Originally, this repository was created for Joel Addison's engineering
major project in 2014 (Supervisors: Peter Sutton (EAIT) and Joel Fenwick).

# Installation
The tool has uses the Boost C++ library in order to function. 
Therefore, in order to install it, a version of Boost needs to be
installed first. To install the Boost library, run the following:

```
./install-boost install.boost.conf
```

The configuration file can be modified as required. Its purpose
is to specify the version of boost to install, as well as where to
install it.

The installation will create the following directory structure at
the chosen location:

```
INSTALL_ROOT/
  + releases/                   <- Contains the zipped downloaded boost library
    + version.tar.bz2
  + extracted/                  <- Contains the content of the library once extracted
    + version/ (e.g. boost_1_73_0)
      + ...
  + builds/                     <- Contains the built library files
    + current                   <- A symlink pointing to the current active build
    + version/ (e.g. 1_73_0)
      + ...
```

Once the Boost library has been installed, `libmarks` can be installed
as follows:

```
./install.sh install.libmarks.conf
```

The configuration file can be modified as required. Its purpose is
to specify the python and boost libraries to use, as well as the 
installation location.

# Using the library
The library uses python files in order to specify test cases.
These python files should contain at least the following to function
correctly

```
!#/usr/bin/env python3
import sys

sys.path[0:0] = ['/path/to/libmarks/install']
import marks    # This must come after the sys.path line

class TestClass(marks.TestCase):
    # One or more classes which extend marks.TestCase 
    # should be present

    @marks.marks('category', category_marks=X)
    def test_someTest(self):
        # Test cases are methods which start with test_
        # which are decorated using the marks.marks decorator
        ...

```
