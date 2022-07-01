# BUILDING VOSK

To use the go bindings you first have to build vosk from source. You can build it by following the instructions on the vosk web site under Compilation from source. https://alphacephei.com/vosk/install

First you will be required to install Kaldi then vosk. Once complete you will have `libvosk.so`.


# INSTALLING VOSK GO BINDINGS


    go get github.com/alphacep/vosk-api/go


# VOSK NOT INSTALLED TO SYSTEM

If the vosk headers aren't installed then use CGO_LDFLAGS environment variable to point to the headers when building and installing.

    CGO_LDFLAGS="-L/opt/vosk-api/src" go get github.com/alphacep/vosk-api/go

    CGO_LDFLAGS="-L/opt/vosk-api/src" go build -o vosk examples/main.go

If the vosk library isn't installed on the system then use the LD_LIBRARY_PATH environment variable to point to the so file when running.

    LD_LIBRARY_PATH=/opt/vosk-api/src ./vosk

