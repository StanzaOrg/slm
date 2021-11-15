#!/usr/bin/env python3

import os
import subprocess
import sys

from subprocess import CalledProcessError

# Keep in sync with `poet.toml`
DEPENDENCIES = {
        "stanza-toml": "tylanphear/stanza-toml|latest",
        "maybe-utils": "tylanphear/maybe-utils|0.0.3",
}

POET_DIR = os.path.join(os.getcwd(), ".poet")
POET_PKGS_DIR = os.path.join(POET_DIR, "pkgs")
POET_DEPS_DIR = os.path.join(POET_DIR, "deps")

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
    # Check for CI PAT for access to private repos
    # (see .github/workflows/main.yml)
    if 'CI_PAT' in os.environ:
        return f"https://tylanphear:{os.environ['CI_PAT']}@github.com/{package}"
    # Otherwise assume user has SSH access to our dependencies
    else:
        return "git@github.com:" + package

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
    dep_proj_files = [
        f"{POET_DEPS_DIR}/{dep}/stanza.proj"
        for dep in DEPENDENCIES.keys()
    ]

    with open(os.path.join(POET_DIR, "stanza.proj"), "w") as f:
        f.writelines([f'include "{proj_file}"\n' for proj_file in dep_proj_files])
        f.write('include "../stanza.proj"\n')

def bootstrap(args):
    # Create bootstrap dir structure
    os.makedirs(POET_DIR)
    os.makedirs(POET_PKGS_DIR)
    os.makedirs(POET_DEPS_DIR)

    # Clone dependencies
    for dependency, identifier in DEPENDENCIES.items():
        package, version = tuple(identifier.split("|"))
        path = os.path.join(POET_DEPS_DIR, dependency)
        fetch_package_into(path, package, version)

    # Generate stanza.proj for build
    generate_stanza_proj()

    # Attempt to build the project and packages
    try:
        check_run(["stanza", "build"] + args, cwd=POET_DIR)
    except CalledProcessError:
        error("Bootstrap failed trying to run `stanza build`")

    poet_path = os.path.join(os.getcwd(), "build", "poet")
    print(f"poet bootstrapped: run `{poet_path} build` to finish building.")

def main(args):
    if os.path.exists(POET_DIR):
        error(f"'{POET_DIR}' exists, was `poet` already bootstrapped?")

    bootstrap(args)

if __name__ == "__main__":
    import sys
    main(sys.argv[1:])
