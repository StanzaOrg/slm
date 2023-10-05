#!/usr/bin/env python3

import os
import subprocess
import sys

from subprocess import CalledProcessError

# Keep in sync with `slm.toml`
DEPENDENCIES = {
        "stanza-toml": "StanzaOrg/stanza-toml|0.3.4",
        "maybe-utils": "StanzaOrg/maybe-utils|0.1.3",
        "semver": "StanzaOrg/semver|0.1.4",
        "term-colors": "StanzaOrg/term-colors|0.1.1",
}

SLM_DIR = os.path.join(os.getcwd(), ".slm")
SLM_PKGS_DIR = os.path.join(SLM_DIR, "pkgs")
SLM_DEPS_DIR = os.path.join(SLM_DIR, "deps")

def error(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)

def check_run (*args, **kwargs):
    kwargs["check"] = True
    kwargs["env"] = os.environ
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
        if not os.path.exists(path):
          check_run(["git", "clone", "--depth", "1", "--quiet", url, path])
        else:
          print(f"Path '{path}' Already Exists - Assuming Clone Already Complete")
        check_run(["git", "fetch", "--tags", "--quiet"], cwd=path)
        check_run(["git", "checkout", "--quiet", "--force", rev], cwd=path)
    except CalledProcessError:
        error(f"failed fetching package {package}")

def generate_stanza_proj():
    dep_proj_files = [
        f"{SLM_DEPS_DIR}/{dep}/stanza.proj"
        for dep in DEPENDENCIES.keys()
    ]

    with open(os.path.join(SLM_DIR, "stanza.proj"), "w") as f:
        f.writelines([f'include "{proj_file}"\n' for proj_file in dep_proj_files])
        f.write('include "../stanza.proj"\n')

def bootstrap(args):
    # Create bootstrap dir structure
    os.makedirs(SLM_DIR, exist_ok=True)
    os.makedirs(SLM_PKGS_DIR, exist_ok=True)
    os.makedirs(SLM_DEPS_DIR, exist_ok=True)

    # Clone dependencies
    for dependency, identifier in DEPENDENCIES.items():
        package, version = tuple(identifier.split("|"))
        path = os.path.join(SLM_DEPS_DIR, dependency)
        fetch_package_into(path, package, version)

    # Generate stanza.proj for build
    generate_stanza_proj()

    # Attempt to build the project and packages
    try:
        check_run(["stanza", "build"] + args, cwd=SLM_DIR)
    except CalledProcessError:
        error("Bootstrap failed trying to run `stanza build`")

    slm_path = os.path.join(os.getcwd(), "slm")
    print(f"slm bootstrapped: run `{slm_path} build` to finish building.")

def main(args):
    bootstrap(args)

if __name__ == "__main__":
    import sys
    main(sys.argv[1:])
