#!/usr/bin/env python3

import os
import subprocess
import sys

from subprocess import CalledProcessError

def eprint(msg):
    print(msg, file=sys.stderr)

if sys.version_info[0] < 3:
    eprint("This script requires python version 3 or greater")
    exit(1)

if sys.version_info[0] == 3 and sys.version_info[1] < 11:
    # The tomllib package was introduced in py3.11 - so
    #  any version before that requires this hack to complete
    #  the bootstrap.
    # Keep in sync with `slm.toml`
    DEPENDENCIES = {
        "stanza-toml": {"git": "StanzaOrg/stanza-toml", "version": "0.3.4"},
        "maybe-utils": {"git": "StanzaOrg/maybe-utils", "version": "0.1.4"},
        "semver": {"git" : "StanzaOrg/semver", "version" : "0.1.6"},
        "term-colors": { "git": "StanzaOrg/term-colors", "version" : "0.1.1"},
    }
else:
    import tomllib
    with open("slm.toml", "rb") as f:
        data = tomllib.load(f)
    DEPENDENCIES = data["dependencies"]

SLM_DIR = os.path.join(os.getcwd(), ".slm")
SLM_PKGS_DIR = os.path.join(SLM_DIR, "pkgs")
SLM_DEPS_DIR = os.path.join(SLM_DIR, "deps")
SLM_PKGCACHE_DIR = os.path.join(SLM_DIR, "pkg-cache")

def error(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)

def check_run (*args, **kwargs):
    kwargs["check"] = True
    subprocess.run(*args, **kwargs)

def version_to_tag(version):
    if version == "latest":
        return "HEAD"
    else:
        return f"v{version}"

def package_to_url(package):
    def git_url(package): return f"git@github.com:{package}"
    def https_url(package): return f"https://github.com/{package}"
    PROTOCOLS = { "git": git_url, "https": https_url, None: git_url }

    return PROTOCOLS[os.environ.get("SLM_PROTOCOL")](package)

def fetch_package_into(path, package, version):
    rev = version_to_tag(version)
    url = package_to_url(package)

    try:
        check_run(["git", "clone", "--depth", "1", "--quiet", url, path])
        check_run(["git", "fetch", "--tags", "--quiet"], cwd=path)
        check_run(["git", "checkout", "--quiet", "--force", rev], cwd=path)
    except CalledProcessError:
        error(f"failed fetching package {package}")

def generate_stanza_proj():
    dep_proj_files = []
    for dep in DEPENDENCIES.keys():
      dep_path = os.path.join(SLM_DEPS_DIR, dep, "stanza.proj")
      # For Windows - we replace the `\` with `/` so that the
      #  'stanza build' invokation will actually run. Otherwise,
      #   stanza treats the `\` as an escape sequence and fails to build.
      #   On Mac/Linux - this should do nothing.
      dep_unnorm = dep_path.replace(os.sep, '/')
      dep_proj_files.append(dep_unnorm)

    with open(os.path.join(SLM_DIR, "stanza.proj"), "w") as f:
        f.writelines([f'include "{proj_file}"\n' for proj_file in dep_proj_files])

def bootstrap(args):
    # Create bootstrap dir structure
    os.makedirs(SLM_DIR)
    os.makedirs(SLM_PKGS_DIR)
    os.makedirs(SLM_DEPS_DIR)
    os.makedirs(SLM_PKGCACHE_DIR)

    # Clone dependencies
    for dependency, specifier in DEPENDENCIES.items():
        package = specifier["git"]
        version = specifier["version"]
        path = os.path.join(SLM_DEPS_DIR, dependency)
        fetch_package_into(path, package, version)

    # Generate stanza.proj for build
    generate_stanza_proj()

    # Attempt to build the project and packages
    try:
        check_run(["stanza", "build"] + args)
    except CalledProcessError:
        error("Bootstrap failed trying to run `stanza build`")

    slm_path = os.path.join(os.getcwd(), "slm")
    print(f"slm bootstrapped: run `{slm_path} build` to finish building.")

def main(args):
    if os.path.exists(SLM_DIR):
        error(f"'{SLM_DIR}' exists, was `slm` already bootstrapped?")

    bootstrap(args)

if __name__ == "__main__":
    import sys
    main(sys.argv[1:])
