#!/usr/bin/env python

from dataclasses import dataclass

import json
import os
import platform
import requests
import sys
import unittest
import urllib.parse

DEFAULT_CONAN_URL = "http://conan.jitx.com:8081/artifactory/api/conan/conan-local"

def eprint(msg):
    print(msg, file=sys.stderr)

def debug(msg):
    pass
    eprint(msg)

if sys.version_info[0] < 3:
    eprint("This script requires python version 3 or greater")
    exit(1)

@dataclass
class ConanVersion:
    """
    A structure for holding all of the components of a fully-qualified conan version

    https://docs.conan.io/2/tutorial/versioning/revisions.html
    """
    name: str
    version: str
    recipe_revision: str = None
    package_id: str = None
    package_revision: str = None

    @staticmethod
    def from_string(s: str):
        """
        A constructor to parse a fully-qualified conan version string into a ConanVersion

        Parameters:
            s: str in the form "a/b#cccccccccccccccccccccccccccccccc:dddddddddddddddddddddddddddddddddddddddd#eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"
                   where only "a/b" is mandatory

        Throws Exception If we fail to parse the version string
        """
        debug(f"ConanVersion: s==\"{s}\"")
        # name before slash
        pslash = s.partition('/')
        name = pslash[0]
        pcolon = pslash[2].partition(':')
        pver = pcolon[0].partition('#')
        ppkg = pcolon[2].partition('#')
        version = pver[0]
        recipe_rev = pver[2] if pver[2] else None
        package_id = ppkg[0] if ppkg[0] else None
        package_rev = ppkg[2] if ppkg[2] else None
        debug(f"ConanVersion( \"{name}\", \"{version}\", \"{recipe_rev}\", \"{package_id}\", \"{package_rev}\")")
        return ConanVersion(name, version, recipe_rev, package_id, package_rev)

    def to_string(self) -> str:
        """
        Convert ConanVersion to a conan-style package version string

        Returns:
            s: str in the form "a/b#cccccccccccccccccccccccccccccccc:dddddddddddddddddddddddddddddddddddddddd#eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"
                   where only "a/b" is mandatory
        """
        s = f"{self.name}/{self.version}"
        if self.recipe_revision is not None:
            s += f"#{self.recipe_revision}"
        if self.package_id is not None:
            s += f":{self.package_id}"
            if self.package_revision is not None:
                s += f"#{self.package_revision}"
        return s



# ------------------------
# --- Conan API syntax ---
# ------------------------
# --- Search for package by name
#  curl $APIBASE/conans/search?q=pcre
#  {
#    "results" : [ "pcre/8.45@_/_" ]
#  }
#
# --- Use results to search for binary packages:
#  curl $APIBASE/conans/pcre/8.45/_/_/search
#  {
#    "139391a944851d9dacf1138cff94b3320d5775dd" : {
#      "settings" : {
#        "os" : "Windows",
#        "compiler.threads" : "posix",
#        "compiler.exception" : "seh",
#        "arch" : "x86_64",
#        "compiler" : "gcc",
#        "build_type" : "Release",
#        "compiler.version" : "11.2"
#      },
#  (...)
#
#  ; list revisions of a package for a specific recipe revision
#  curl -v 'http://conan.jitx.com:8081/artifactory/api/conan/conan-local/v2/conans/pcre/8.45/_/_/revisions/125d5f684fea10391ff4cbcd809a5c74/packages/6f7dea16aa97d9ca0f6b67b413781234ab190708/revisions'
#
# --- Use hash to get download url
#  curl $APIBASE/conans/pcre/8.45/_/_/packages/139391a944851d9dacf1138cff94b3320d5775dd/download_urls
#  {
#    "conaninfo.txt" : "http://localhost:8082/artifactory/api/conan/conan-local/v2/files/_/pcre/8.45/_/125d5f684fea10391ff4cbcd809a5c74/package/139391a944851d9dacf1138cff94b3320d5775dd/ce6f2349e761f6350cbde62b02a687c7/conaninfo.txt",
#    "conan_package.tgz" : "http://localhost:8082/artifactory/api/conan/conan-local/v2/files/_/pcre/8.45/_/125d5f684fea10391ff4cbcd809a5c74/package/139391a944851d9dacf1138cff94b3320d5775dd/ce6f2349e761f6350cbde62b02a687c7/conan_package.tgz",
#    "conanmanifest.txt" : "http://localhost:8082/artifactory/api/conan/conan-local/v2/files/_/pcre/8.45/_/125d5f684fea10391ff4cbcd809a5c74/package/139391a944851d9dacf1138cff94b3320d5775dd/ce6f2349e761f6350cbde62b02a687c7/conanmanifest.txt"
#  }
#
# --- Use the url for "conan_package.tgz"
#  http://localhost:8082/artifactory/api/conan/conan-local/v2/files/_/pcre/8.45/_/125d5f684fea10391ff4cbcd809a5c74/package/139391a944851d9dacf1138cff94b3320d5775dd/ce6f2349e761f6350cbde62b02a687c7/conan_package.tgz


def urlenc(s: str) -> str:
    """Urlencode the given string"""
    return urllib.parse.quote_plus(s)

def conan_search_package_name(package_name: str, **kwargs) -> json:
    """
    Search for the given package name on the conan server

    Parameters:
      package_name: str The package name to find.  Only the name, no version components.
    kwargs:
      repourl: str The repo to search.  Optional, Default DEFAULT_CONAN_URL.

    Returns: json results

    throws Exception on invalid json returned
    """
    repourl = kwargs["repourl"] if "repourl" in kwargs else DEFAULT_CONAN_URL
    queryurl = f"{repourl}/v2/conans/search"
    headers = {"Content-Type": "application/json"}
    params = {"q": package_name}

    response = requests.get(queryurl, headers=headers, params=params)
    return json.loads(response.text)


def conan_get_recipe_revisions(package_name: str, package_version: str, **kwargs) -> dict:
    """
    Search for the available recipe revisions for the given package name on the conan server

    Parameters:
        package_name
        package_version
    kwargs:
      repourl: str The repo to search.  Optional, Default DEFAULT_CONAN_URL.

    throws Exception on invalid json returned
    """
    repourl = kwargs["repourl"] if "repourl" in kwargs else DEFAULT_CONAN_URL
    queryurl = f"{repourl}/v2/conans/{urlenc(package_name)}/{urlenc(package_version)}/_/_/revisions"
    headers = {"Content-Type": "application/json"}

    response = requests.get(queryurl, headers=headers)
    jresult = json.loads(response.text)
    if "errors" in jresult:
      raise Exception("Conan error while getting recipe revisions for \"{package_name}/{package_version}\": \"{jresult}\"")
    return jresult["revisions"]


def conan_get_package_ids_for_revision(package_name: str, package_version: str, recipe_revision: str, **kwargs) -> dict:
    """
    Search for the available package_ids for the given package name and recipe revision on the conan server

    Parameters:
        package_name
        package_version
        recipe_revision
    kwargs:
      repourl: str The repo to search.  Optional, Default DEFAULT_CONAN_URL.

    throws Exception on invalid json returned
    """
    repourl = kwargs["repourl"] if "repourl" in kwargs else DEFAULT_CONAN_URL
    # search for available package_ids of the recipe revision
    queryurl = f"{repourl}/v2/conans/{urlenc(package_name)}/{urlenc(package_version)}/_/_/revisions/{urlenc(recipe_revision)}/search"
    headers = {"Content-Type": "application/json"}

    response = requests.get(queryurl, headers=headers)
    jresult = json.loads(response.text)
    if "errors" in jresult:
      raise Exception("Conan error while getting package_ids for recipe revision \"{package_name}/{package_version}#{recipe_revision}\": \"{jresult}\"")
    return jresult


def conan_get_package_revisions(package_name: str, package_version: str, recipe_revision: str, package_id: str, **kwargs) -> dict:
    """
    Search for available package revisions of the given recipe revision and package_id

    Parameters:
        package_name
        package_version
        recipe_revision
        package_id
    kwargs:
      repourl: str The repo to search.  Optional, Default DEFAULT_CONAN_URL.

    throws Exception on invalid json returned
    """
    repourl = kwargs["repourl"] if "repourl" in kwargs else DEFAULT_CONAN_URL
    # search for available package_ids of the recipe revision
    queryurl = f"{repourl}/v2/conans/{urlenc(package_name)}/{urlenc(package_version)}/_/_/" + \
               f"revisions/{urlenc(recipe_revision)}/packages/{urlenc(package_id)}/revisions"
    headers = {"Content-Type": "application/json"}

    response = requests.get(queryurl, headers=headers)
    jresult = json.loads(response.text)
    if "errors" in jresult:
      raise Exception("Conan error while getting package revisions for package_id \"{package_name}/{package_version}#{recipe_revision}\": \"{jresult}\"")
    return jresult["revisions"]


def conan_fully_qualify_latest_version(cv: ConanVersion, **kwargs) -> ConanVersion:
    """
    Searches the given conan repository for the latest package matching the given ConanVersion and options.

    Parameters:
        package_name
        package_version
        recipe_revision
        package_id
    kwargs:
      options: dictionary of key/value options.  Optional, Default empty dictionary.
      repourl: str The repo to search.  Optional, Default DEFAULT_CONAN_URL.

    throws Exception on failure or package not found
    """

    debug(f"conan_fully_qualify_latest_version: qualifying version: {cv.to_string()}")
    # If the cv has already has all of the parts, then return it unchanged
    if not (cv.package_id is None or cv.recipe_revision is None or cv.package_revision is None):
        return cv
    else:
        package_name = cv.name
        package_version = cv.version
        options = kwargs["options"] if "options" in kwargs else {}

        current_conan_os = platform.system()
        if current_conan_os == "Darwin":
            current_conan_os = "Macos"

        # search for available recipe revisions using just the name and version
        for rr in conan_get_recipe_revisions(package_name, package_version, **kwargs):
            recipe_revision = rr["revision"]
            recipe_revision_time = rr["time"]
            debug(f"conan-fully_qualify_latest_version: recipe_revision: \"{recipe_revision}\" on \"{recipe_revision_time}\"")

            for package_id, package_info in conan_get_package_ids_for_revision(package_name, package_version, recipe_revision, **kwargs).items():
                ### package_info format:
                # {
                # "settings":     {
                #         "os":   "Windows",
                #         "compiler.threads":     "posix",
                #         "compiler.exception":   "seh",
                #         "arch": "x86_64",
                #         "compiler":     "gcc",
                #         "build_type":   "Release",
                #         "compiler.version":     "11.2"
                # },
                # "options":      {
                #         "build_pcrecpp":        "False",
                #         "build_pcre_16":        "False",
                #         "build_pcre_8": "True",
                #         "shared":       "True",
                #         "with_stack_for_recursion":     "True",
                #         "build_pcregrep":       "False",
                #         "build_pcre_32":        "False",
                #         "with_utf":     "True",
                #         "with_unicode_properties":      "True",
                #         "with_jit":     "False"
                # }

                # look for packages compiled for the current os we're running on
                # TODO this could be improved with arch and compiler checks
                #      but for now just check os
                package_settings_os = package_info["settings"]["os"]
                if package_settings_os != current_conan_os:
                    # not our os
                    debug(f"conan_fully_qualify_latest_version: package \"{package_id}\" os = \"{package_settings_os}\" [SKIP]")
                else:
                    debug(f"conan_fully_qualify_latest_version: package \"{package_id}\" os = \"{package_settings_os}\" [ok]")

                    # ensure the desired options match this package's options
                    if options == package_info["settings"]:
                        # this package matches our os and the requested options
                        # get the latest revision for this package
                        for pr in conan_get_package_revisions(package_name, package_version, recipe_revision, package_id, **kwargs):
                            package_revision = pr["revision"]
                            package_revision_time = pr["time"]
                            debug(f"conan_fully_qualify_latest_version: package_revision: \"{package_revision}\" on \"{package_revision_time}\"")

                            # NOTE: assuming that the most recent revision is listed first
                            # if this turns out not to be the case, then sort by package_revision_time
                            fqcv = ConanVersion(package_name, package_version, recipe_revision, package_id, package_revision)
                            debug(f"conan_fully_qualify_latest_version: found \"{fqcv}\"")
                            return(fqcv)
                    else:
                        debug(f"conan_fully_qualify_latest_version: options \"{options}\" doesn't match \"{package_info['settings']}\"")


    # if we reach here, we didn't find a match
    raise Exception("conan search could not find matching package for options")


def conan_download_package(cv: ConanVersion, **kwargs) -> str :
    """
    returns path to downloaded file

    Parameters:
        package_name
        package_version
        recipe_revision
        package_id
    kwargs:
      target_directory: directory to save the downloaded file into. Optional, Default current directory.
      repourl: str The repo to search.  Optional, Default DEFAULT_CONAN_URL.

    throws Exception on failure or package not found
    """
    debug(f"conan_download_package: downloading version: {cv.to_string()}")
    target_directory = kwargs["target_directory"] if "target_directory" in kwargs else "."
    repourl = kwargs["repourl"] if "repourl" in kwargs else DEFAULT_CONAN_URL

    fqcv = conan_fully_qualify_latest_version(cv, **kwargs)

    if cv.package_id is None or cv.recipe_revision is None or cv.package_revision is None:
      raise Exception("conan version must be fully specified with revisions and package_ids")

    downloadurl = f"{repourl}/v2/conans/{urlenc(cv.name)}/{urlenc(cv.version)}/_/_/" + \
                  f"revisions/{urlenc(cv.recipe_revision)}/packages/{urlenc(cv.package_id)}/revisions/{urlenc(cv.package_revision)}/files/conan_package.tgz"
    headers = {"Content-Type": "application/json"}
    debug(f"conan_download_package: downloadurl: \"{downloadurl}\"")

    outfile = f"{target_directory}/conan_package_{fqcv.name}_{fqcv.version}_{fqcv.package_id}.tgz"
    debug("conan_download_package: outfile: \"{outfile}\"")

    # download url to file
    r = requests.get(downloadurl, stream=True)
    with open(outfile, 'wb') as fd:
        for chunk in r.iter_content(chunk_size=128):
            fd.write(chunk)

    return outfile


### Tests ######################################################################

class TestConanVersion(unittest.TestCase):
    online=True  # set to True to enable online tests

    def test_repr(self):
        cv = ConanVersion("foo", "1.2.3")
        self.assertEqual(repr(cv), "ConanVersion(name='foo', version='1.2.3', recipe_revision=None, package_id=None, package_revision=None)")
        self.assertEqual(repr(cv), str(cv))

        cv = ConanVersion("bar", "5.6.7", "d41d8cd98f00b204e9800998ecf8427e", "da39a3ee5e6b4b0d3255bfef95601890afd80709", "da39a3ee5e6b4b0d3255bfef95601890afd80709")
        roundtrip = eval(repr(cv))
        self.assertEqual(str(cv), str(roundtrip))

    def test_from_string(self):
        cv = ConanVersion.from_string("foo/1.2.3")
        self.assertEqual(repr(cv), "ConanVersion(name='foo', version='1.2.3', recipe_revision=None, package_id=None, package_revision=None)")
        self.assertEqual(repr(cv), str(cv))

        cv = ConanVersion.from_string("bar/5.6.7#d41d8cd98f00b204e9800998ecf8427e:da39a3ee5e6b4b0d3255bfef95601890afd80709#da39a3ee5e6b4b0d3255bfef95601890afd80709")
        roundtrip = eval(repr(cv))
        self.assertEqual(str(cv), str(roundtrip))

    def test_to_string(self):
        s = "foo/1.2.3"
        self.assertEqual(ConanVersion.from_string(s).to_string(), s)

        s = "foo/1.2.3#d41d8cd98f00b204e9800998ecf8427e"
        self.assertEqual(ConanVersion.from_string(s).to_string(), s)

        s = "foo/1.2.3:da39a3ee5e6b4b0d3255bfef95601890afd80709"
        self.assertEqual(ConanVersion.from_string(s).to_string(), s)

        s = "foo/1.2.3:da39a3ee5e6b4b0d3255bfef95601890afd80709#da39a3ee5e6b4b0d3255bfef95601890afd80709"
        self.assertEqual(ConanVersion.from_string(s).to_string(), s)

        s = "bar/5.6.7#d41d8cd98f00b204e9800998ecf8427e:da39a3ee5e6b4b0d3255bfef95601890afd80709#da39a3ee5e6b4b0d3255bfef95601890afd80709"
        self.assertEqual(ConanVersion.from_string(s).to_string(), s)
        cv = ConanVersion.from_string("bar/5.6.7#d41d8cd98f00b204e9800998ecf8427e:da39a3ee5e6b4b0d3255bfef95601890afd80709#da39a3ee5e6b4b0d3255bfef95601890afd80709")
        roundtrip = ConanVersion.from_string(cv.to_string())
        self.assertEqual(str(cv), str(roundtrip))

    @unittest.skipUnless(online==True, "not online")
    def test_conan_search_package_name(self):
        # note: results dependent on what is on the server
        r = conan_search_package_name("pcre")
        self.assertEqual(r, {'results': ['pcre/8.45@_/_']})

    @unittest.skipUnless(online==True, "not online")
    def test_conan_get_recipe_revisions(self):
        # note: results dependent on what is on the server
        r = conan_get_recipe_revisions("pcre", "8.45")
        self.assertEqual(r, [{'revision': '125d5f684fea10391ff4cbcd809a5c74', 'time': '2024-02-17T00:31:04.551+0000'},
                             {'revision': '64cdfd792761c32817cd31d7967c3709', 'time': '2024-02-16T21:58:05.694+0000'}])

    @unittest.skipUnless(online==True, "not online")
    def test_conan_get_package_ids_for_revision(self):
        # note: results dependent on what is on the server
        r = conan_get_package_ids_for_revision("pcre", "8.45", "125d5f684fea10391ff4cbcd809a5c74")
        self.assertEqual(r, {
            '139391a944851d9dacf1138cff94b3320d5775dd': {
                'settings': {
                    'os': 'Windows',
                    'compiler.threads': 'posix',
                    'compiler.exception': 'seh',
                    'arch': 'x86_64',
                    'compiler': 'gcc',
                    'build_type': 'Release',
                    'compiler.version': '11.2'
                },
                'options': {
                    'build_pcrecpp': 'False',
                    'build_pcre_16': 'True',
                    'build_pcre_8': 'True',
                    'shared': 'False',
                    'with_bzip2': 'True',
                    'with_stack_for_recursion': 'True',
                    'build_pcregrep': 'True',
                    'build_pcre_32': 'True',
                    'with_utf': 'True',
                    'with_unicode_properties': 'True',
                    'with_zlib': 'True',
                    'with_jit': 'False'
                },
                'content': '[settings]\narch=x86_64\nbuild_type=Release\ncompiler=gcc\ncompiler.exception=seh\ncompiler.threads=posix\n'+
                           'compiler.version=11.2\nos=Windows\n[options]\nbuild_pcre_16=True\nbuild_pcre_32=True\nbuild_pcre_8=True\n'+
                           'build_pcrecpp=False\nbuild_pcregrep=True\nshared=False\nwith_bzip2=True\nwith_jit=False\nwith_stack_for_recursion=True\n'+
                           'with_unicode_properties=True\nwith_utf=True\nwith_zlib=True\n[requires]\nbzip2/1.0.Z\nzlib/1.2.Z\n',
                'requires': []
            },
            '22df55d12fd0a729491762b4508bc4ddf8b50a38': {
                'settings': {
                    'os': 'Linux',
                    'arch': 'x86_64',
                    'compiler': 'gcc',
                    'build_type': 'Release',
                    'compiler.version': '11'
                },
                'options': {
                    'build_pcrecpp': 'False',
                    'build_pcre_16': 'True',
                    'build_pcre_8': 'True',
                    'shared': 'False',
                    'with_bzip2': 'True',
                    'with_stack_for_recursion': 'True',
                    'build_pcregrep': 'True',
                    'build_pcre_32': 'True',
                    'fPIC': 'True',
                    'with_unicode_properties': 'True',
                    'with_zlib': 'True',
                    'with_jit': 'False',
                    'with_utf': 'True'
                },
                'content': '[settings]\narch=x86_64\nbuild_type=Release\ncompiler=gcc\ncompiler.version=11\nos=Linux\n[options]\n'+
                           'build_pcre_16=True\nbuild_pcre_32=True\nbuild_pcre_8=True\nbuild_pcrecpp=False\nbuild_pcregrep=True\n'+
                           'fPIC=True\nshared=False\nwith_bzip2=True\nwith_jit=False\nwith_stack_for_recursion=True\n'+
                           'with_unicode_properties=True\nwith_utf=True\nwith_zlib=True\n[requires]\nbzip2/1.0.Z\nzlib/1.2.Z\n',
                'requires': []
            },
            '6f7dea16aa97d9ca0f6b67b413781234ab190708': {
                'settings': {
                    'os': 'Macos',
                    'arch': 'x86_64',
                    'compiler': 'apple-clang',
                    'build_type': 'Release',
                    'compiler.version': '13'
                },
                'options': {
                    'build_pcrecpp': 'False',
                    'build_pcre_16': 'True',
                    'build_pcre_8': 'True',
                    'shared': 'False',
                    'with_bzip2': 'True',
                    'with_stack_for_recursion': 'True',
                    'build_pcregrep': 'True',
                    'build_pcre_32': 'True',
                    'fPIC': 'True',
                    'with_unicode_properties': 'True',
                    'with_zlib': 'True',
                    'with_jit': 'False',
                    'with_utf': 'True'
                },
                'content': '[settings]\narch=x86_64\nbuild_type=Release\ncompiler=apple-clang\ncompiler.version=13\nos=Macos\n'+
                           '[options]\nbuild_pcre_16=True\nbuild_pcre_32=True\nbuild_pcre_8=True\nbuild_pcrecpp=False\n'+
                           'build_pcregrep=True\nfPIC=True\nshared=False\nwith_bzip2=True\nwith_jit=False\n'+
                           'with_stack_for_recursion=True\nwith_unicode_properties=True\nwith_utf=True\nwith_zlib=True\n'+
                           '[requires]\nbzip2/1.0.Z\nzlib/1.2.Z\n',
                'requires': []
            }
        })

    @unittest.skipUnless(online==True, "not online")
    def test_conan_get_package_revisions(self):
        # note: results dependent on what is on the server
        r = conan_get_package_revisions("pcre", "8.45", "125d5f684fea10391ff4cbcd809a5c74", "22df55d12fd0a729491762b4508bc4ddf8b50a38")
        self.assertEqual(r,
            [{'revision': '5a5560f797885024ff7e6a48b3b7543e', 'time': '2024-02-17T00:31:04.944+0000'}]
        )

    @unittest.skipUnless(online==True, "not online")
    def test_conan_fully_qualify_latest_version(self):
        # note: results dependent on what is on the server
        r = conan_fully_qualify_latest_version(ConanVersion.from_string("pcre/8.45"),
                                               options = {
                                                   'os': 'Linux',
                                                   'arch': 'x86_64',
                                                   'compiler': 'gcc',
                                                   'build_type': 'Release',
                                                   'compiler.version': '11'})
        self.assertEqual(r,
            ConanVersion( "pcre", "8.45", "125d5f684fea10391ff4cbcd809a5c74", "22df55d12fd0a729491762b4508bc4ddf8b50a38", "5a5560f797885024ff7e6a48b3b7543e")
        )

    @unittest.skipUnless(online==True, "not online")
    def test_conan_download_package(self):
        # note: results dependent on what is on the server
        n = "pcre"
        v = "8.45"
        pid = "22df55d12fd0a729491762b4508bc4ddf8b50a38"
        expected_name = f"./conan_package_{n}_{v}_{pid}.tgz"
        if os.path.exists(expected_name):
            os.remove(expected_name)
        self.assertFalse( os.path.isfile(expected_name) )
        cv = conan_fully_qualify_latest_version(ConanVersion.from_string(f"{n}/{v}:{pid}"),
                                                options = {
                                                    'os': 'Linux',
                                                    'arch': 'x86_64',
                                                    'compiler': 'gcc',
                                                    'build_type': 'Release',
                                                    'compiler.version': '11'})
        dlp = conan_download_package(cv)
        self.assertEqual(dlp, expected_name)
        self.assertTrue( os.path.isfile(dlp) and os.stat(dlp).st_size > 0 )
        os.remove(dlp)


if __name__ == "__main__":
    # self-test
    unittest.main()
