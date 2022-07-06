# Installation

- go get github.com/alphacep/vosk-api

# Compiling

- Download latest release https://github.com/alphacep/vosk-api/releases
- Unzip archive containing
- CGO_ENABLED=1 CGO_CPPFLAGS="-I /path/to/archive_directory" CGO_LDFLAGS="-L /path/to/archive_directory -lvosk -ldl -lpthread" go build .

# Running

- Working directory need to contain libvosk