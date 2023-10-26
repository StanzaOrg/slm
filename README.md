# Overview

`slm` is a package manager for [Stanza](http://lbstanza.org/).

# Requirements

- Linux with glibc 2.31 or newer
- Stanza 0.16.3 or newer
- Git 2.6.7 or newer

# Installation

Just download a release from [releases](https://github.com/StanzaOrg/slm/releases), and put it on your `$PATH` somewhere.

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
stanza-toml = "StanzaOrg/stanza-toml|0.3.4"
semver      = "StanzaOrg/semver|0.1.4"
maybe-utils = "StanzaOrg/maybe-utils|0.1.4"
term-colors = "StanzaOrg/term-colors|0.1.1"
```

## Build

To build a `slm` package, use `slm build`. This will create the `.slm` directory if necessary, fetch any dependencies as specified in your `slm.toml`, and then invoke `stanza build`, forwarding it any arguments given. It will also create a `slm.lock` file alongside your `slm.toml` that encapsulates the state of your dependencies at build time, so that subsequent builds do not have to fetch dependencies anew.

`slm` will define the `SLM_BUILD_VERSION` environment variable in the context of the `stanza build` process. This environment variable will be populated with the value of the `version` key from the `slm.toml` file for the project being built. This allows the project being built to incorporate this version number in any library or executable that it generates. See
the `slm/commands/version` package for an example of how to use this in your project.

## Publish

To publish a `slm` package, use `slm publish`. For now, you must also have set an upstream (for example, by using `git branch -u <upstream-repo-url>`) for the branch you are on. You must also be in a clean state (no outstanding changes). `slm` will `git tag` the current version (as specified in your `slm.toml`) and then push it to your upstream.

## Clean

To clean a `slm` package, use `slm clean`. This removes any fetched dependencies and clears your build cache.

# Caveats

Packages that use `slm` must be built using `slm build`, and cannot be built using `stanza build`. Attempting to do so will most likely result in various compile errors due to the build system not pulling in packages from your dependencies.

This is in part due to the fact that the Stanza build system is not capable of fetching packages (like `slm build`), but also because a `slm`-compatible `stanza.proj` does not reference the main `.slm/stanza.proj` or `stanza.proj` files from dependent packages in any way. This is mostly not an issue in practice, but something to be aware of if you run into this issue.
