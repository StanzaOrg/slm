#!/bin/sh

set -eu

./bootstrap.py

./slm clean
./slm build

# Build the tests

./slm build tests
./slm-tests