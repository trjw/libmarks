#!/usr/bin/env python

from distutils.core import setup, Extension
import subprocess

from distutils.command.install import install as DistutilsInstall

class BoostLibInstall(DistutilsInstall):
    def run(self):
        makeProc=subprocess.Popen('make');
        rc=makeProc.wait()
        #raise OSError()
        if rc != 0:
            raise OSError()
        DistutilsInstall.run(self)

        print("post", file=sys.stderr);

boostMacros = [('BOOST_BIND_GLOBAL_PLACEHOLDERS', '1')]
boostLibs = ['boost_python-py36']

moduleProcess = Extension('marks.process', sources=['src/process.cpp', 'src/glue.cpp', 
                                             'src/traced_process.cpp'],
                            libraries = boostLibs,
                            define_macros = boostMacros)
moduleProtect = Extension('libprotect', sources=['src/protection.c'])

setup(name='marks', version='1.0',
        description='CSSE2310 libmarks',
        author='various',
        packages=['marks'],
        ext_modules = [moduleProcess, moduleProtect],
        #cmdclass={'install': BoostLibInstall},
        )
