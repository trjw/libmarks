#!/usr/bin/env bash
#
# A wrapper for installing libmarks
#
# Usage: install.sh /path/to/install/config
#
# The configuration file has the following format:
#
#   install_root  = /path/to/install/location
#
#   py_version    = XX (e.g. 3.8)
#   py_include    = /path/to/python/include/files (e.g. /usr/include/python3.8)
#   py_libname    = pythonXX                      (e.g python3.8)
#   py_lib        = /path/to/python/lib           (e.g. /usr/lib/python3.8)
#
#   boost_inc     = /path/to/boost/lib/include    (e.g. .../boost/version/include)
#   boost_lib     = /path/to/boost/lib/lib        (e.g. .../boost/version/lib)
#   boost_libname = boost_pythonXX                (e.g. boost_python38)
SCRIPT_PATH="$( cd "$(dirname "$0")" > /dev/null 2>&1; pwd -P )"

if [ $# -ne 1 ]; then
    echo "Usage: install.sh /path/to/config"
    exit 1
fi

# First, we load the configuration from the config file
CONF_PATH=$1
if [ ! -f ${CONF_PATH} ]; then
    echo "Invalid configuration file path specified"
    exit 1
fi
source ${CONF_PATH}

# Next, we need to check that the expected values have been set
expected_py_vars=('py_version' 'py_include' 'py_libname' 'py_lib')
expected_boost_vars=('boost_inc' 'boost_lib' 'boost_libname')

if [ -z "${install_root+x}" ]; then
    echo "Configuration does not specify an installation destination (install_root)"
    exit 1
fi

for var in "${expected_py_vars[@]}"; do
    if [ -z "${var+x}" ]; then
        echo "Configuration does not specify python variable: ${var}"
        exit 1
    fi
done

for var in "${expected_boost_vars[@]}"; do
    if [ -z "${var+x}" ]; then
        echo "Configuration does not specify boost variable: ${var}"
        exit 1
    fi
done

echo "About to install libmarks with the following configuration"
echo "----"
printf "%19s: %s\n" "install destination" ${install_root}
echo ""
for var in "${expected_py_vars[@]}"; do
    printf "%19s: %s\n" ${var} ${!var}
done
echo ""
for var in "${expected_boost_vars[@]}"; do
    printf "%19s: %s\n" ${var} ${!var}
done
echo "----"
while true; do
    read -p "Do you wish to continue installation? [Y/N] " yn
    case $yn in
        [Yy] ) break;; 
        * ) exit;;
    esac
done

mkdir -p ${install_root}/marks
make \
    -C ${SCRIPT_PATH}/src/libmarks \
    -f ${SCRIPT_PATH}/src/libmarks/Makefile \
    INSTALL_DEST=${install_root}/marks \
    BOOST_INC=${boost_inc} BOOST_LIB=${boost_lib} BOOST_LIBNAME=${boost_libname} \
    PYTHON_INCLUDE=${py_include} PYTHON_LIB=${py_lib} PYTHON_LIBNAME=${py_libname} \
    install clean
