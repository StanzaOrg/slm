# Overview

`poet` is a package manager for [Stanza](http://lbstanza.org/).

# Requirements

- Linux with glibc 2.31 or newer
- Stanza 0.16.3 or newer
- Git 2.6.7 or newer

# Installation

Just download a release from [releases](https://github.com/tylanphear/poet/releases), and put it on your `$PATH` somewhere.

# Usage

To initialize a `poet` package, use `poet init`. This will initialize a Git repository into the given directory, and create a basic package structure comprising the `.poet` directory and `poet.toml`. If a directory is not specified, the current directory is used. This command can be used to create an entirely new package, or to create a package from an existing project, and *will not* overwrite any of your existing files.

To build a `poet` package, use `poet build`. This will create the `.poet` directory if necessary, fetch any dependencies as specified in your `poet.toml`, and then invoke `stanza build`, forwarding it any arguments given. It will also create a `poet.lock` file alongside your `poet.toml` that encapsulates the state of your dependencies at build time, so that subsequent builds do not have to fetch dependencies anew.

To publish a `poet` package, use `poet publish`. For now, you must also have set an upstream (for example, by using `git branch -u <upstream-repo-url>`) for the branch you are on. You must also be in a clean state (no outstanding changes). `poet` will `git tag` the current version (as specified in your `poet.toml`) and then push it to your upstream.

To clean a `poet` package, use `poet clean`. This removes any fetched dependencies and clears your build cache.

# Caveats

Packages that use `poet` must be built using `poet build`, and cannot be built using `stanza build`. Attempting to do so will most likely result in various compile errors due to the build system not pulling in packages from your dependencies.

This is in part due to the fact that the Stanza build system is not capable of fetching packages (like `poet build`), but also because a `poet`-compatible `stanza.proj` does not reference the main `.poet/stanza.proj` or `stanza.proj` files from dependent packages in any way. This is mostly not an issue in practice, but something to be aware of if you run into this issue.
