#!/bin/bash
#
# Script to run the conan build and generate the required packages
#
# Current usage of Conan is kind of a hack. We're not having conan
#  to run the `stanza build`. This means I have to get the binary
#  to the package some how and Conan makes this more difficult than
#  just copying it to a file. I don't get access to the `recipe_folder`
#  after the `export_sources` function. But I can't copy the binary in
#  `export_sources_folder` because anything in that directory gets hashed
#  as part of the repository id.
#
# I must pass this directory as an environment variable
#  so that each run of `conanfile.py` gets the same directory.
export SLM_ROOT_DIR=$(pwd)
conan create .