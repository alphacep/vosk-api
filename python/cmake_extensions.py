# From https://github.com/raydouglass/cmake_setuptools

# See https://cmake.org/cmake/help/latest/manual/cmake.1.html for cmake CLI options

import os
import subprocess
import shutil
import sys
from glob import glob
from setuptools import Extension
from setuptools.command.build_ext import build_ext
from setuptools.command.build_py import build_py
from setuptools.command.install_lib import install_lib

CMAKE_EXE = os.environ.get('CMAKE_EXE', shutil.which('cmake'))


def check_for_cmake():
    if not CMAKE_EXE:
        print('cmake executable not found. '
              'Set CMAKE_EXE environment or update your path')
        sys.exit(1)


class CMakeExtension(Extension):
    """
    setuptools.Extension for cmake
    """

    def __init__(self, name, pkg_name, sourcedir=''):
        check_for_cmake()
        Extension.__init__(self, name, sources=[])
        self.sourcedir = os.path.abspath(sourcedir)
        self.pkg_name = pkg_name


class CMakeBuildExt(build_ext):
    """
    setuptools build_exit which builds using cmake & make
    You can add cmake args with the CMAKE_COMMON_VARIABLES environment variable
    """

    def build_extension(self, ext: Extension):
        check_for_cmake()
        if isinstance(ext, CMakeExtension):
            output_dir = os.path.abspath(
                os.path.dirname(self.get_ext_fullpath(ext.pkg_name + "/" + ext.name)))

            build_type = 'Debug' if self.debug else 'Release'
            cmake_args = [CMAKE_EXE,
                          '-S', ext.sourcedir,
                          '-B', self.build_temp,
                          '-Wno-dev',
                          '--debug-output',
                          '-DPython_EXECUTABLE=' + sys.executable.replace("\\", "/"),
                          '-DCMAKE_VERBOSE_MAKEFILE:BOOL=ON',
                          '-DCMAKE_LIBRARY_OUTPUT_DIRECTORY=' + output_dir.replace("\\", "/"),
                          '-DCMAKE_BUILD_TYPE=' + build_type]
            cmake_args.extend(
                [x for x in
                 os.environ.get('CMAKE_COMMON_VARIABLES', '').split(' ')
                 if x])

            env = os.environ.copy()
            self.announce('Generating native project files: {}'.format(cmake_args), level=4)
            subprocess.check_call(cmake_args, env=env)

            build_args = [CMAKE_EXE, '--build', self.build_temp]

            # This ugly hack is needed because CMake Visual Studio generator ignores CMAKE_BUILD_TYPE and creates
            # Debug (default) and Release configurations. When building, the first one is chosen by default.
            # For some reason, setting CMAKE_CONFIGURATION_TYPES inside CMakeLists.txt leads to error MSB8020 during build.
            if os.name == 'nt':
                build_args.extend(['--config', build_type])

            self.announce('Building: {}'.format(build_args), level=4)
            subprocess.check_call(build_args, env=env)

            libs = sum([
                glob(os.path.join(self.build_temp, pattern), recursive=True)
                for pattern in ('**/*.so', '**/*.pyd')
            ], [])
            self.announce('Build created {} in {}; they will be copied to {}'.format(libs, self.build_temp, output_dir), level=4)
            os.makedirs(output_dir, exist_ok=True)
            for lib in libs:
                shutil.copy(lib, output_dir)
        else:
            super().build_extension(ext)


class CMakeBuildExtFirst(build_py):
    def run(self):
        self.run_command("build_ext")
        return super().run()


__all__ = ['CMakeBuildExt', 'CMakeExtension', 'CMakeBuildExtFirst']
