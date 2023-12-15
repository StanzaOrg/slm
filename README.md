# Overview

`slm` is a package manager for [Stanza](http://lbstanza.org/).

# Requirements

- Linux with glibc 2.31 or newer
- Stanza 0.18.52 or newer
- Git 2.28.0 or newer

# Installation

Just download a release from [releases](https://github.com/StanzaOrg/slm/releases), and put it on your `$PATH` somewhere.

## Building from Source

To build SLM from source you will need to bootstrap the build environment. The
`bootstrap.py` file contains a python3 script that will setup the dependencies
for the build and call `stanza`

Requirements:

1.  Python 3.11 or greater available on your system.
2.  Stanza 0.18.52 availble on the `$PATH`

Then you can run:

```
$> python3 bootstrap.py
slm bootstrapped: run `slm build` to finish building.
$> ./slm build
slm: syncing semver to 0.1.6
slm: syncing term-colors to 0.1.1
slm: syncing stanza-toml to 0.3.4
slm: syncing maybe-utils to 0.1.4
```

Once complete the `slm` binary located in the local directory is ready for use.

# Usage

The `slm` command has several sub-commands that are used to accomplish the build process.

## Initialize

To initialize a `slm` package, use `slm init`. This will initialize a Git repository into the given directory, and create a basic package structure comprising the `.slm` directory and `slm.toml`. If a directory is not specified, the current directory is used. This command can be used to create an entirely new package, or to create a package from an existing project, and *will not* overwrite any of your existing files.

### `slm.toml` Structure

Here is a typical `slm.toml` file structure:

```toml
name = "slm"
version = "0.3.2"

[dependencies]
stanza-toml.git     = "StanzaOrg/stanza-toml"
stanza-toml.version = "0.3.4"
semver.git          = "StanzaOrg/semver"
semver.version      = "0.1.4"
maybe-utils.git     = "StanzaOrg/maybe-utils"
maybe-utils.version = "0.1.4"
term-colors.git     = "StanzaOrg/term-colors"
term-colors.version = "0.1.1"

```

## Build

To build a `slm` package, use `slm build`. This will create the `.slm` directory if necessary, fetch any dependencies as specified in your `slm.toml`, and then invoke `stanza build`, forwarding it any arguments given. It will also create a `slm.lock` file alongside your `slm.toml` that encapsulates the state of your dependencies at build time, so that subsequent builds do not have to fetch dependencies anew.

`slm` will define the `SLM_BUILD_VERSION` environment variable in the context of the `stanza build` process. This environment variable will be populated with the value of the `version` key from the `slm.toml` file for the project being built. This allows the project being built to incorporate this version number in any library or executable that it generates. See
the `slm/commands/version` package for an example of how to use this in your project.

## Repl

You can use slm to handle dependency resolution before launching the repl as well:

```
$> slm repl src/main.stanza
REPL environment is now inside package basic/main.
stanza>
```

## Publish

To publish a `slm` package, use `slm publish`. For now, you must also have set an upstream (for example, by using `git branch -u <upstream-repo-url>`) for the branch you are on. You must also be in a clean state (no outstanding changes). `slm` will `git tag` the current version (as specified in your `slm.toml`) and then push it to your upstream.

## Clean

To clean a `slm` package, use `slm clean`. This removes any fetched dependencies and clears your build cache.

## Working directly with `stanza`

You can also call `stanza build` or `stanza repl` directly once you have
resolved dependencies once using `slm build` or `slm repl`.

# Building a Conan2 Package

To build the Conan2 package for binary distribution of `slm`:

1.  Build the `slm` utility as described above.
1.  Setup the Python Environment
    1.  Use python 3.11 or higher
    2.  `python3 -m venv venv`
    3.  `source venv/bin/activate`
    4.  `pip install -r requirements.txt`
2.  Setup the conan build:
    1.  [Optional] Define the `CONAN_HOME` environment variable:
        1.  `export CONAN_HOME=$PWD/.conan2`
    2.  Create or confirm that you have a conan profile installed
        1.  Create: `conan profile detect`
            1.  This will create a profile by guessing based on your system configuration.
        2.  Confirm: `conan profile show -pr default`
            1.  This will show the default configuration.
3.  Run the conan build:
    1.  `conan create . -s os="Macos" -s arch="x86_64"`
    2.  You can replace os with `Windows` or `Linux`
    3.  No Promises on `Windows` build working yet.
4.  Publish the package:
    1.  `conan remote add <NAME> <URL>`
        1.  You should only have to do this once.
    2.  `conan remote login <NAME> <USER> -p <PASSWD>`
    3.  `conan upload -r <NAME> slm/<VERSION>`

