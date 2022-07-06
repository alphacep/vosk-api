# Installation

- Download latest release https://github.com/alphacep/vosk-api/releases
- Unzip archive containing
- go get github.com/alphacep/vosk-api

# Compiling

- CGO_ENABLED=1 CGO_LDFLAGS="-L /path/to/libvosk -lvosk -ldl -lpthread" go build .

# Running 

- Working directory need to contain libvosk