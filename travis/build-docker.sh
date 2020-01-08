#!/bin/bash

set -e
set -x

docker build --file Dockerfile.manylinux --tag alphacep/kaldi-manylinux:latest .
