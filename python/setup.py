import os
import setuptools
import shutil
import glob
import platform

# Figure out environment for cross-compile
vosk_source = os.getenv("VOSK_SOURCE", os.path.abspath(os.path.join(os.path.dirname(__file__),
    "..")))
system = os.environ.get('VOSK_SYSTEM', platform.system())
architecture = os.environ.get('VOSK_ARCHITECTURE', platform.architecture()[0])
machine = os.environ.get('VOSK_MACHINE', platform.machine())

# Copy precompmilled libraries
for lib in glob.glob(os.path.join(vosk_source, "src/lib*.*")):
    print ("Adding library", lib)
    shutil.copy(lib, "vosk")

# Create OS-dependent, but Python-independent wheels.
try:
    from wheel.bdist_wheel import bdist_wheel
except ImportError:
    cmdclass = {}
else:
    class bdist_wheel_tag_name(bdist_wheel):
        def get_tag(self):
            abi = 'none'
            if system == 'Darwin':
                oses = 'macosx_10_6_universal2'
            elif system == 'Windows' and architecture == '32bit':
                oses = 'win32'
            elif system == 'Windows' and architecture == '64bit':
                oses = 'win_amd64'
            elif system == 'Linux' and machine == 'aarch64' and architecture == '64bit':
                oses = 'manylinux2014_aarch64'
            elif system == 'Linux':
                oses = 'linux_' + machine
            else:
                raise TypeError("Unknown build environment")
            return 'py3', abi, oses
    cmdclass = {'bdist_wheel': bdist_wheel_tag_name}

with open("README.md", "rb") as fh:
    long_description = fh.read().decode("utf-8")

setuptools.setup(
    name="vosk",
    version="0.3.50",
    author="Alpha Cephei Inc",
    author_email="contact@alphacephei.com",
    description="Offline open source speech recognition API based on Kaldi and Vosk",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/alphacep/vosk-api",
    packages=setuptools.find_packages(),
    package_data = {'vosk': ['*.so', '*.dll', '*.dyld']},
    entry_points = {
        'console_scripts': ['vosk-transcriber=vosk.transcriber.cli:main'],
    },
    include_package_data=True,
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        'Operating System :: MacOS :: MacOS X',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    cmdclass=cmdclass,
    python_requires='>=3',
    zip_safe=False, # Since we load so file from the filesystem, we can not run from zip file
    setup_requires=['cffi>=1.0', 'requests', 'tqdm', 'srt', 'websockets'],
    install_requires=['cffi>=1.0', 'requests', 'tqdm', 'srt', 'websockets'],
    cffi_modules=['vosk_builder.py:ffibuilder'],
)
