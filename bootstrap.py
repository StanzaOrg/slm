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
        "curl_static":              { "git": "StanzaOrg/slm_curl",              "version": "0.0.1" },
        "file_system_utils_static": { "git": "StanzaOrg/slm_file_system_utils", "version": "0.0.1" },
        "json_static":              { "git": "StanzaOrg/slm_json",              "version": "0.0.1" },
        "maybe-utils":              { "git": "StanzaOrg/maybe-utils",           "version": "0.1.4" },
        "semver":                   { "git": "StanzaOrg/semver",                "version": "0.1.6" },
        "stanza-toml":              { "git": "StanzaOrg/stanza-toml",           "version": "0.4.0" },
        "term-colors":              { "git": "StanzaOrg/term-colors",           "version": "0.1.1" },
        "libcurl": { "pkg": "libcurl", "type": "conan", "version": "8.6.0",
            "options": {
                "shared": "False",
                "with_brotli": "False",
                "with_c_ares": "False",
                "with_ca_bundle": "auto",
                "with_ca_fallback": "False",
                "with_ca_path": "auto",
                "with_cookies": "True",
                "with_crypto_auth": "True",
                "with_dict": "True",
                "with_docs": "False",
                "with_file": "True",
                "with_ftp": "True",
                "with_gopher": "True",
                "with_http": "True",
                "with_imap": "True",
                "with_ipv6": "True",
                "with_largemaxwritesize": "False",
                "with_ldap": "False",
                "with_libgsasl": "False",
                "with_libidn": "False",
                "with_libpsl": "False",
                "with_librtmp": "False",
                "with_libssh2": "False",
                "with_mqtt": "True",
                "with_nghttp2": "False",
                "with_ntlm": "True",
                "with_ntlm_wb": "True",
                "with_pop3": "True",
                "with_proxy": "True",
                "with_rtsp": "True",
                "with_smb": "True",
                "with_smtp": "True",
                "with_ssl": "openssl",
                "with_symbol_hiding": "False",
                "with_telnet": "True",
                "with_tftp": "True",
                "with_threaded_resolver": "True",
                "with_unix_sockets": "True",
                "with_verbose_debug": "True",
                "with_verbose_strings": "True",
                "with_zlib": "True",
                "with_zstd": "False",
                "linux": {
                    "fPIC": "True",
                    "with_ssl": "openssl"
                },
                "macos": {
                    "fPIC": "True",
                    "with_ssl": "darwinssl"
                },
                "windows": {
                    "with_ssl": "schannel",
                    "with_unix_sockets": "False"
                }
            }
        }
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
        eprint(f"slm bootstrap: fetching {package} {version} into {path}")
        check_run(["git", "clone", "--depth", "1", "--quiet", url, path])
        check_run(["git", "fetch", "--tags", "--quiet"], cwd=path)
        check_run(["git", "checkout", "--quiet", "--force", rev], cwd=path)
    except CalledProcessError:
        error(f"failed fetching package {package}")

def download_conan_package_into(path, package, version, options):
    import bootstrap_conan_utils as bcu
    import tarfile

    eprint(f"slm bootstrap: downloading \"{package}/{version}\" with options \"{options}\"")
    cv = bcu.ConanVersion(package, version)
    cv = bcu.conan_fully_qualify_latest_version(cv, options=options)
    pfilename = bcu.conan_download_package(cv)
    eprint(f"downloaded \"{pfilename}\", extracting to {path}")

    tarfile.open(pfilename).extractall(path)

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
        f.writelines([f'include? "{proj_file}"\n' for proj_file in dep_proj_files])

def bootstrap(args):
    # Create bootstrap dir structure
    os.makedirs(SLM_DIR)
    os.makedirs(SLM_PKGS_DIR)
    os.makedirs(SLM_DEPS_DIR)
    os.makedirs(SLM_PKGCACHE_DIR)

    # Clone dependencies
    for dependency, specifier in DEPENDENCIES.items():
        eprint(f"dep \"{dependency}\" = \"{specifier}\"")
        path = os.path.join(SLM_DEPS_DIR, dependency)
        if "git" in specifier:
            package = specifier["git"]
            version = specifier["version"]
            fetch_package_into(path, package, version)
        elif "pkg" in specifier and "type" in specifier and specifier["type"]=="conan":
            package = specifier["pkg"]
            version = specifier["version"]
            options = specifier["options"]
            download_conan_package_into(path, package, version, options)
        else:
            raise Exception(f"unknown dependency type: \"{dependency}\" = \"{specifier}\"")

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
