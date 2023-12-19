import sys
V = sys.version_info
if V[0] < 3:
   raise RuntimeError("Invalid Python Version - This script expects at least Python 3")

if V[0] == 3 and (V[1] < 11):
  raise RuntimeError("Invalid Python Version - This scripts expect at least version Python 3.11")

import os
import platform
from conan import ConanFile
from conan.tools.files import copy
import tomllib

SLM_FOLDER = None

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

    def get_bin_name(self):
        # NOTE - the 'self.settings.os' isn't available in
        #  export sources on windows for some reason - hence why I'm trying to
        #  determine what name to use in a different way.
        name = "slm"
        if platform.system() == "Windows":
            return f"{name}.exe"
        else:
            return name

    def dist_files(self):
       return [
          self.get_bin_name(),
          "LICENSE"
       ]

    def copy_dist_files(self, src_dir, dst_dir):
        success = []
        for f in self.dist_files():
            cp_files = copy(self, f, src_dir, dst_dir)
            success.extend(cp_files)

        if len(success) != len(self.dist_files()):
          raise RuntimeError("Export: Failed to Copy Distribution Files")

    # def export_sources(self):
    #     # Anything copied to the export sources folder will
    #     #  get hashed to create the repository id. We want this
    #     #  to be consistent from OS to OS.
    #  TODO - When we get the `stanza build` running through conan
    #    We would copy sources here and then run the build.

    def build(self):
        SLM_FOLDER = os.environ["SLM_ROOT_DIR"]
        self.copy_dist_files(SLM_FOLDER, self.build_folder)

    def package(self):
        # Slight deviation here - I want the binary in the `bin`
        #   directory and the LICENSE at the top level of the package
        BIN_DIR = os.path.join(self.package_folder, "bin")
        copy(self, self.get_bin_name(), self.build_folder, BIN_DIR)
        copy(self, "LICENSE", self.build_folder, self.package_folder)




