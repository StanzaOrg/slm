#!/usr/bin/env python3

import os
import subprocess
import sys

# Keep in sync with `poet.toml`
DEPENDENCIES = {
        "stanza-toml": "git@github.com:tylanphear/stanza-toml|latest",
        "maybe-utils": "git@github.com:tylanphear/maybe-utils|0.0.3",
}

POET_DIR = os.path.join(os.getcwd(), ".poet")

def version_to_tag(version):
    if version == "latest":
        return "HEAD"
    else:
        return f"v{version}"

# kind of a hack, but SSH authentication doesn't always work, whereas HTTPS
# always will
def ssh_to_https(url):
    url = url.replace("git@", "https://")
    url = url.replace("github.com:", "github.com/")
    return url

def git_clone(path, url, rev):
    url = ssh_to_https(url)
    subprocess.run(["git", "clone", "--depth", "1", "--quiet", url, path])
    subprocess.run(["git", "fetch", "--tags", "--quiet"], cwd=path)
    subprocess.run(["git", "checkout", "--quiet", "--force", rev], cwd=path)

def generate_stanza_proj():
    proj_files = \
            [os.path.join(POET_DIR, "deps", d, "stanza.proj") for d in DEPENDENCIES]
    root_proj_file = os.path.join("..", "stanza.proj")

    with open(os.path.join(POET_DIR, "stanza.proj"), "w") as f:
        f.writelines([f'include "{proj_file}"\n' for proj_file in proj_files])
        f.write(f'include "{root_proj_file}"\n')

def run_stanza_build():
    os.makedirs(os.path.join(POET_DIR, "pkgs"))
    subprocess.run(["stanza", "build", "-pkg", "pkgs"], cwd=POET_DIR)

def main():
    if os.path.exists(POET_DIR):
        print(f"'{POET_DIR}' exists, was `poet` already bootstrapped?", file=sys.stderr)
        sys.exit(1)

    # Create bootstrap dir
    os.makedirs(POET_DIR)

    # Clone dependencies
    for dependency, identifier in DEPENDENCIES.items():
        url, version = tuple(identifier.split("|"))
        path = os.path.join(POET_DIR, "deps", dependency)
        rev = version_to_tag(version)

        git_clone(path, url, rev)

    generate_stanza_proj()
    run_stanza_build()
    poet_path = os.path.join(os.getcwd(), "poet")
    print(f"poet bootstrapped: run `{poet_path} build` to finish building.")

if __name__ == "__main__":
    main()
