import os
import setuptools
import subprocess
from cmake import *

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="vosk", # Replace with your own username
    version=subprocess.check_output(["git", "describe"]).strip().decode("utf-8"),
    author="Alpha Cephei Inc",
    author_email="contact@alphacephei.com",
    description="API for Kaldi and Vosk",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/alphacep/vosk-api",
    packages=setuptools.find_packages(),
    ext_modules=[CMakeExtension('_vosk', 'vosk')],
    cmdclass={'build_ext': CMakeBuildExt, 'build_py' : CMakeBuildExtFirst},
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        'Operating System :: MacOS :: MacOS X',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    python_requires='>=3.4',
)
