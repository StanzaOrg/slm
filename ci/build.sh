#!/bin/sh

set -eu

./bootstrap.py

# work around windows git read-only files by making them writable
OSTYPE=${OSTYPE:-unknown}
case "$OSTYPE" in
  msys* | cygwin*)
      /usr/bin/find .slm -not -perm /u+w -exec chmod u+w {} + ;;
esac

./slm clean
./slm build

# Build the tests

./slm build tests
./slm-tests
