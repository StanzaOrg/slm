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

def ssh_to_https(url):
    url = url.replace("git@", "https://")
    url = url.replace("github.com:", "github.com/")
    return url

def git_clone(path, url, rev):
    # kind of a hack: SSH won't work without authentication -- use HTTPS
    # instead. As long as we only depend on public repos, this will work.
    url = ssh_to_https(url)
    subprocess.run(["git", "clone", "--depth", "1", "--quiet", url, path])
    subprocess.run(["git", "fetch", "--tags", "--quiet"], cwd=path)
    subprocess.run(["git", "checkout", "--quiet", "--force", rev], cwd=path)

def generate_stanza_proj():
    root_proj_file = os.path.join("..", "stanza.proj")

    proj_files = [
        os.path.join(POET_DIR, "deps", d, "stanza.proj")
        for d in DEPENDENCIES
    ]
    proj_files.append(root_proj_file) # should come last

    with open(os.path.join(POET_DIR, "stanza.proj"), "w") as f:
        f.writelines([f'include "{proj_file}"\n' for proj_file in proj_files])

def run_stanza_build(args):
    os.makedirs(os.path.join(POET_DIR, "pkgs"))
    p = subprocess.run(["stanza", "build", "-pkg", "pkgs"] + args, cwd=POET_DIR)
    if p.returncode != 0:
        print("Bootstrap failed trying to run `stanza build`", file=sys.stderr)
        sys.exit(1)

def main(args):
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
    run_stanza_build(args)

    poet_path = os.path.join(os.getcwd(), "poet")
    print(f"poet bootstrapped: run `{poet_path} build` to finish building.")

if __name__ == "__main__":
    import sys
    main(sys.argv[1:])
