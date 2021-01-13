#!/usr/bin/env bash
#
# A script for installing the boost python
# libraries to work with libmarks
if [ $# -ne 1 ]; then
    echo "Usage: install-boost.sh /path/to/config"
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
expected_vars=('boost_version' 'install_root')
for var in "${expected_vars[@]}"; do
    if [ -z "${var+x}" ]; then
        echo "Configuration does not specify variable: ${var}"
        exit 1
    fi
done

echo "About to install boost with the following configuration"
echo "----"
for var in "${expected_vars[@]}"; do
    printf "%13s: %s\n" ${var} ${!var}
done
echo "----"
while true; do
    read -p "Do you wish to continue installation? [Y/N] " yn
    case $yn in
        [Yy] ) break;; 
        * ) exit;;
    esac
done

BOOST_ROOT=${install_root}
BOOST_VERSION=${boost_version}

FILE_VERSION=$(echo ${BOOST_VERSION} | sed 's/\./_/g')
FILE_NAME="boost_${FILE_VERSION}"
SRC_URL="https://dl.bintray.com/boostorg/release/${BOOST_VERSION}/source/${FILE_NAME}.tar.bz2"

# First we need to make build the boost library structure
# if it doesn't already exist
mkdir -p ${BOOST_ROOT}
mkdir -p ${BOOST_ROOT}/releases
mkdir -p ${BOOST_ROOT}/extracted
mkdir -p ${BOOST_ROOT}/builds

# Once we have our structure set up, we need to get a copy
# of the boost library (if we haven't done so already)
if [ ! -f "${BOOST_ROOT}/releases/${FILE_NAME}.tar.bz2" ]; then
    echo "No existing boost library found. Downloading a new copy."
    wget --no-verbose -P ${BOOST_ROOT}/releases ${SRC_URL}
fi

# Now that we have our copy, we need to extract and build it
# Note that if we've built it before, the old copy will be overwritten
echo "Extracting boost library files."
tar --bzip2 -xf ${BOOST_ROOT}/releases/${FILE_NAME}.tar.bz2 -C ${BOOST_ROOT}/extracted

# Once the files have been extracted, we need to run the bootstrap script
# to generate the files we require. Note that the old files will be overwritten
echo "Building boost library."
current_dir=$(pwd)
cd ${BOOST_ROOT}/extracted/${FILE_NAME}

rm -rf ${BOOST_ROOT}/builds/${FILE_VERSION}

./bootstrap.sh \
    --prefix=${BOOST_ROOT}/builds/${FILE_VERSION} \
    --exec-prefix=${BOOST_ROOT}/builds/${FILE_VERSION} \
    --with-python=/usr/bin/python3 \
    --with-libraries=system,thread,filesystem,exception,python

./b2 include='/usr/bin/python3.8' install

# Now that the build has been made, we also update the current build symlink
echo "Updating symlinks."
cd ${BOOST_ROOT}/builds
if [ -f current ]; then
    rm -f current
fi
ln -s ${FILE_VERSION} current

echo "Done."