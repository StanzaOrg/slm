import sys

V = sys.version_info
if V[0] < 3:
   raise RuntimeError("Invalid Python Version - This script expects at least Python 3")

if V[0] == 3 and (V[1] < 11):
  raise RuntimeError("Invalid Python Version - This scripts expect at least version Python 3.11")

import os
from conan import ConanFile
from conan.tools.files import copy
import tomllib

def get_slm_config(fp = "./slm.toml"):
    with open(fp, "rb") as f:
      data = tomllib.load(f)
    return data

class slmRecipe(ConanFile):
    """ Conan2 Recipe to create a distribution package for `slm`
    Note that I don't do any building here - I just use the output of
    the stanza build and copy it into a package.
    """
    name = "slm"
    package_type = "application"

    # Optional metadata
    license = "BSD 3-Clause"
    author = "Carl Allendorph (c.allendorph@jitx.com)"
    url = "https://github.com/StanzaOrg/slm"
    description = "Stanza Library Manager"
    topics = ("stanza", "lbstanza", "library management", "package management")

    # Binary configuration
    settings = "os", "arch"

    def set_version(self):
      # Extract the version information from the `slm.toml` file
      #  so that we don't have to synchronize two sources.
      cfg_path = os.path.join(self.recipe_folder, "slm.toml")
      config = get_slm_config(cfg_path)
      self.version = config["version"]

    def layout(self):
        _os = str(self.settings.os).lower()
        _arch = str(self.settings.arch).lower()
        print(f"OS: {_os}   Arch: {_arch}")
        self.folders.build = "build"

    def export_sources(self):
        exp_files = copy(self, "slm", self.recipe_folder, self.export_sources_folder)
        if len(exp_files) == 0:
          raise RuntimeError("Export: Failed to Copy SLM Binary")

    def build(self):
        build_files = copy(self, "slm", self.export_sources_folder, self.build_folder)
        if len(build_files) == 0:
          raise RuntimeError("Build:Failed to Copy SLM Binary")

    def package(self):
        BIN_DIR = os.path.join(self.package_folder, "bin")
        print(f"BinDir: {BIN_DIR}")
        cp_files = copy(self, "slm", self.build_folder, BIN_DIR)
        if len(cp_files) == 0:
          raise RuntimeError("Package:Failed to Copy SLM Binary")




