
import sys
V=sys.version_info
if V[0] < 3 or (V[0] == 3 and V[1] < 11):
  raise RuntimeError("Invalid Python Version - This script expects at least Python 3.11")

import os
import platform
import tomllib
from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import can_run
from conan.tools.files import copy
from conan.tools.cmake import CMakeDeps, CMakeToolchain
from conan.tools.env import VirtualBuildEnv
from pathlib import Path
from shutil import copy2, copytree, which

required_conan_version = ">=2.0"

class ConanSlmPackage(ConanFile):
  package_type = "application"
  python_requires = "lbstanzagenerator_pyreq/[>=0.6.20 <0.7.0]"

  # Binary configuration
  #settings = "os", "arch", "compiler", "build_type"
  settings = "os", "arch"

  # hide all dependencies from consumers
  # https://blog.conan.io/2024/07/09/Introducing-vendoring-packages.html
  vendor = True


  # set_name(): Dynamically define the name of a package
  def set_name(self):
    self.output.info("conanfile.py: set_name()")
    with open(f"{self.recipe_folder}/slm.toml", "rb") as f:
        self.name = tomllib.load(f)["name"]
    self.output.info(f"conanfile.py: set_name() - self.name={self.name} from slm.toml")


  # set_version(): Dynamically define the version of a package.
  def set_version(self):
    self.output.info("conanfile.py: set_version()")
    with open(f"{self.recipe_folder}/slm.toml", "rb") as f:
        self.version = tomllib.load(f)["version"]
    self.output.info(f"conanfile.py: set_version() - self.version={self.version} from slm.toml")


  # validate_build(): Verify if a package binary can be built with the current configuration
  def validate_build(self):
    self.output.info("conanfile.py: validate_build()")

    # if codesigning is enabled
    if self.conf.get("user.jitx.slm:codesign") and self.settings.os == "Windows":
      # Verify that the required environment variables and programs exist
      ### required environment variables for authentication with DigiCert
      # example: SM_API_KEY="00000000000000000000000000_0000000000000000000000000000000000000000000000000000000000000000"
      # example: SM_CLIENT_CERT_FILE="C:\Users\Administrator\.signingmanager\jwatson-digicert-clientcert-20231212-Certificate_pkcs12.p12"
      # example: SM_CLIENT_CERT_PASSWORD="xxxxxxxxxxxx"
      # example: SM_KEY_ALIAS="key_000000000"
      # example: SMCTL="C:\Program Files\DigiCert\DigiCert Keylocker Tools\smctl.exe"
      VARERR=0
      for V in ["SM_API_KEY", "SM_CLIENT_CERT_FILE", "SM_CLIENT_CERT_PASSWORD", "SM_KEY_ALIAS", "SMCTL"]:
        if V not in os.environ:
          self.output.error(f"conanfile.py: validate_build(): codesigning environment variable {V} not found")
          VARERR=1
      if VARERR > 0:
        raise ConanInvalidConfiguration("Required code signing configuration not found")
      for V in ["SM_CLIENT_CERT_FILE", "SMCTL"]:
        if not os.path.exists(os.getenv(V)):
          self.output.error(f"conanfile.py: validate_build(): codesigning {V} file \"{os.getenv(V)}\" does not exist")
          VARERR=1
      if not which("signtool"):
          self.output.error(f"conanfile.py: validate_build(): codesigning file \"signtool\" is not on PATH")
          VARERR=1
      if VARERR > 0:
        raise ConanInvalidConfiguration("Required code signing configuration not found")


  # export(): Copies files that are part of the recipe
  def export(self):
    self.output.info("conanfile.py: export()")
    # export slm.toml with the conan recipe so that it can be referenced at dependency time without sources
    copy(self, "slm.toml", self.recipe_folder, self.export_folder)


  # export_sources(): Copies files that are part of the recipe sources
  def export_sources(self):
    self.output.info("conanfile.py: export_sources()")
    copy2(os.path.join(self.recipe_folder, "slm.toml"), self.export_sources_folder)
    #lock = os.path.join(self.recipe_folder, "slm.lock")
    #if os.path.exists(lock):
    #  copy2(lock, self.export_sources_folder)
    # copy template stanza proj files, if any
    for f in Path(".").glob("template-stanza-*.proj"):
        copy2(os.path.join(self.recipe_folder, f), self.export_sources_folder)
    copy2(os.path.join(self.recipe_folder, "stanza.proj"), self.export_sources_folder)
    for f in Path(".").glob("stanza-library.proj"):
        copy2(os.path.join(self.recipe_folder, f), self.export_sources_folder)
    copytree(os.path.join(self.recipe_folder, "ci"), os.path.join(self.export_sources_folder, "ci"))
    copytree(os.path.join(self.recipe_folder, "src"), os.path.join(self.export_sources_folder, "src"))
    copytree(os.path.join(self.recipe_folder, "tests"), os.path.join(self.export_sources_folder, "tests"))


  # configure(): Allows configuring settings and options while computing dependencies
  def configure(self):
    self.output.info("conanfile.py: configure()")

    with open(f"{self.recipe_folder}/slm.toml", "rb") as f:
      deps = tomllib.load(f)["dependencies"]
      # get current platform
      psys = platform.system().lower()
      if psys=="darwin":
        psys = "macos"

      # for each dependency in slm.toml
      for k, d in deps.items():
        # if it's a conan pkg dependency
        if "pkg" in d.keys() and "type" in d.keys() and d["type"]=="conan":
          # get its name and set any options
          pkgname = d["pkg"]

          if "options" in d.keys():
            opts = d["options"]
            for k, v in opts.items():
              self.output.trace(f"conanfile.py: configure() options[\"{pkgname}\"].{k}={v}")
              # check for platform-specific options
              if k in ["linux", "macos", "windows"]:
                # only apply our platform, skip others
                if k==psys:
                  for k2, v2 in v.items():
                    self.options[pkgname]._set(k2,v2)
              else:
                self.options[pkgname]._set(k,v)


  # requirements(): Define the dependencies of the package
  def requirements(self):
    self.output.info("conanfile.py: requirements()")

    with open(f"{self.recipe_folder}/slm.toml", "rb") as f:
      deps = tomllib.load(f)["dependencies"]

      # for each dependency in slm.toml
      for k, d in deps.items():
        # if it's a conan pkg dependency
        if "pkg" in d.keys() and "type" in d.keys() and d["type"]=="conan":
          # use its name and version as a conan requires
          pkgname = d["pkg"]
          pkgver = d["version"]

          # package_id_mode="unrelated_mode" means don't list this required lib in the
          # requirements for the slm output package
          self.output.trace(f"conanfile.py: requirements() requires(\"{pkgname}/{pkgver}\", package_id_mode=\"unrelated_mode\")")
          self.requires(f"{pkgname}/{pkgver}", package_id_mode="unrelated_mode")


  # build_requirements(): Defines tool_requires and test_requires
  def build_requirements(self):
    self.output.info("conanfile.py: build_requirements()")
  
    # use stanza provided by conan
    self.tool_requires("lbstanza/[>=0.18.78 <1.0]")
    self.tool_requires(f"slm/[>=0.6.22 <{self.version}]")

    # use cmake and ninja provided by conan
    # necessary if compiling non-stanza dependencies
    self.tool_requires("cmake/[>=3.20 <4.0]")
    self.tool_requires("ninja/[>=1.11 <2.0]")
  
    # use mingw-builds compiler provided by conan on windows
    if self.settings.os == "Windows":
      self.tool_requires("mingw-builds/11.2.0")


  # generate(): Generates the files that are necessary for building the package
  def generate(self):
    self.output.info("conanfile.py: generate()")
    lbsg = self.python_requires["lbstanzagenerator_pyreq"].module.LBStanzaGenerator(self).generate()

    # NOTE: slm and stanza are not in PATH in the conanfile.generate() method
    #self.run("pwd ; ls -la", cwd=None, ignore_errors=False, env="", quiet=False, shell=True, scope="build")


  # build(): Contains the build instructions to build a package from source
  def build(self):
    self.output.info("conanfile.py: build()")
    self.run("bash -c 'pwd ; ls -la'", cwd=self.source_folder, scope="build")
    self.run("stanza version", cwd=self.source_folder, scope="build")
    self.run("slm version", cwd=self.source_folder, scope="build")
    self.run("bash -c '[ ! -d .slm ] || slm clean'", cwd=self.source_folder, scope="build")
    self.run("slm build -verbose -- -verbose", cwd=self.source_folder, scope="build")

    if not self.conf.get("tools.build:skip_test", default=False):
      d="build"
      t="test"
      self.run(f"stanza clean", cwd=self.source_folder, scope="build")
      self.run(f"stanza build {t} -o {d}/{t} -verbose", cwd=self.source_folder, scope="build")
      update_path_cmd=""
      if platform.system()=="Darwin":
        # on macos, find all dlls in the current directory recursively, and add their directories to the DYLD_LIBRARY_PATH so that the dlls can be located at runtime
        # get a unique set of directories that contain dlls under the current directory
        dylib_dirs = {p.resolve().parents[0].as_posix() for p in sorted(Path('.').glob('**/*.dylib'))}
        path_str = ':'.join(dylib_dirs)
        if path_str:
          update_path_cmd=f"export DYLD_LIBRARY_PATH={path_str}:$DYLD_LIBRARY_PATH ; "
      elif platform.system()=="Windows":
        t="test.exe"
        # on windows, find all dlls in the current directory recursively, and add their directories to the PATH so that the dlls can be located at runtime
        # get a unique set of directories that contain dlls under the current directory
        dll_win_dirs = {p.resolve().parents[0].as_posix() for p in sorted(Path('.').glob('**/*.dll'))}
        # convert those windows-style paths to bash-style paths
        dll_bash_dirs = [f"/{d[0].lower()}{d[2:]}" for d in dll_win_dirs]
        # make a path-style string of those bash-style paths
        path_str = ':'.join(dll_bash_dirs)
        if path_str:
          update_path_cmd=f"export PATH={path_str}:$PATH ; "
      self.run(f"bash -c '{update_path_cmd} {d}/{t}'",
               cwd=self.source_folder, scope="build")


  # _codesign(): Internal function to sign the executables
  def _codesign(self):
    self.output.info("conanfile.py: _codesign()")
    self.run("ls -la", cwd=self.source_folder, scope="build")
    self.run("bash -e ci/sign-windows-release.bash", cwd=self.source_folder, scope="build")


  # package(): Copies files from build folder to the package folder.
  def package(self):
    self.output.info("conanfile.py: package()")
    outerlibname = self.name.removeprefix("slm-")

    if self.conf.get("user.jitx.slm:codesign") and self.settings.os == "Windows":
      self._codesign()

    copy2(os.path.join(self.source_folder, "slm.toml"), self.package_folder)
    #copy2(os.path.join(self.source_folder, "slm.lock"), self.package_folder)
    copy2(os.path.join(self.source_folder, f"stanza-{outerlibname}-relative.proj"), os.path.join(self.package_folder, f"stanza-{outerlibname}.proj"))
    copy2(os.path.join(self.source_folder, "stanza.proj"), os.path.join(self.package_folder, "stanza.proj"))
    copytree(os.path.join(self.source_folder, "src"), os.path.join(self.package_folder, "src"))

    # copy slm executable from the build directory to /bin/
    slm="slm"
    if platform.system()=="Windows":
        slm += ".exe"
    Path(os.path.join(self.package_folder, "bin")).mkdir(parents=True, exist_ok=True)
    copy2(os.path.join(self.source_folder, slm), os.path.join(self.package_folder, "bin"))

    # copy any libraries from the lib build directory to /lib/
    Path(os.path.join(self.package_folder, "lib")).mkdir(parents=True, exist_ok=True)
    for f in Path("lib").glob("*.a"):
        copy2(os.path.join(self.source_folder, f), os.path.join(self.package_folder, "lib"))
    for f in Path("lib").glob("*.dll"):
        copy2(os.path.join(self.source_folder, f), os.path.join(self.package_folder, "lib"))
    for f in Path("lib").glob("*.dylib"):
        copy2(os.path.join(self.source_folder, f), os.path.join(self.package_folder, "lib"))
    for f in Path("lib").glob("*.so"):
        copy2(os.path.join(self.source_folder, f), os.path.join(self.package_folder, "lib"))
