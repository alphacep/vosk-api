import os
import sys
import setuptools
import shutil
import glob

vosk_source = os.getenv("VOSK_SOURCE", os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
print(vosk_source)
for lib in glob.glob(os.path.join(vosk_source, "src/lib*.*")):
    print ("Adding library", lib)
    shutil.copy(lib, "vosk")

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="vosk",
    version="0.3.18",
    author="Alpha Cephei Inc",
    author_email="contact@alphacephei.com",
    description="Offline open source speech recognition API based on Kaldi and Vosk",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/alphacep/vosk-api",
    packages=setuptools.find_packages(),
    package_data = {'vosk': ['*.so', '*.dll']},
    include_package_data=True,
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        'Operating System :: MacOS :: MacOS X',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    python_requires='>=3',
    zip_safe=False, # Since we load so file from the filesystem, we can not run from zip file
    setup_requires=['cffi>=1.0'],
    install_requires=['cffi>=1.0'],
    cffi_modules=['vosk_builder.py:ffibuilder'],
)
