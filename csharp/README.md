This is a nuget-based wrapper for libvosk library

See demo folder for example how to use the library. You can simply run
"dotnet run" to run the demo. Make sure you unpacked the model and the
test file.

See the nuget folder for the sources of the wrapper. Run build.sh to
build nuget package.

Note we only support win64 and linux64 for now. No support for win32
since it is a little bit painful to load the libraries depending on
architecture. In theory we can add OSX some time or even Android.
