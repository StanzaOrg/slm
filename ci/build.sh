#!/bin/sh

set -eu

./bootstrap.py

./poet clean
./poet build
