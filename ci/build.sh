#!/bin/sh

set -eu

./bootstrap.py

./slm clean
./slm build
