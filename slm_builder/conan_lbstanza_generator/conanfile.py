
# Conan L.B.Stanza Generator
# https://docs.conan.io/2/reference/extensions/custom_generators.html

from conan import ConanFile
from conan.tools.files import save
from io import TextIOWrapper
from pathlib import Path

class LBStanzaGeneratorPyReq(ConanFile):
    name = "lbstanzagenerator_pyreq"
    version = "0.6.20"
    package_type = "python-require"

# LBStanza Generator class
class LBStanzaGenerator:

    def __init__(self, conanfile):
        self._conanfile = conanfile

    def get_libs_from_component(self, compname: str, compinst) -> dict[str, str]:
        #breakpoint()
        self._conanfile.output.trace(f"      - {compname}")

        reqlibdirs = compinst.libdirs
        self._conanfile.output.trace(f"        - libdirs = {reqlibdirs}")

        self._conanfile.output.trace(f"        - libs:")
        libdict = {}
        for l in compinst.libs:
            self._conanfile.output.trace(f"          - {l}")

            libdict[l] = [Path(r) for r in reqlibdirs]

        #breakpoint()
        self._conanfile.output.trace(f"        - get_libs_from_component(\"{compname}\", inst) -> \"{libdict}\"")
        return libdict

    def write_package_fragment(self, is_shared_lib: bool, include_dirs: list[str], libs: dict, outfilename: str):
        self._conanfile.output.trace(f"  > write_package_fragment({is_shared_lib},")
        self._conanfile.output.trace(f"      libs[\"linux\"] = \"{libs['linux']}\",")
        self._conanfile.output.trace(f"      libs[\"macos\"] = \"{libs['macos']}\",")
        self._conanfile.output.trace(f"      libs[\"windows\"] = \"{libs['windows']}\",")
        self._conanfile.output.trace(f"      \"{outfilename}\")")
        outerlibname = self._conanfile.name.removeprefix("slm-")
        with open(outfilename, 'w') as outf:
            # look for a file called "template-stanza-{outerlibname}.proj", and include its contents if it exists.
            # this is because all "package requires" statements for a stanza package must be in the same file.
            # and it's cleaner to include them in this file fragment rather than put these fragment contents into the top-level stanza.proj
            templatefile = f"template-stanza-{outerlibname}.proj"
            package_requires_found = False
            package_tests_requires_found = False
            if Path(templatefile).exists():
                self._conanfile.output.trace(f"Including contents of template file \"{templatefile}\"")
                with open(templatefile, 'r') as t:
                    for line in t:
                        # look for the package requires line so we can skip it later
                        if f"package {outerlibname} requires" in line:
                            package_requires_found = True
                        elif f"package {outerlibname}/tests requires" in line:
                            package_tests_requires_found = True
                        outf.write(line)
            else:
                self._conanfile.output.trace(f"Optional template file \"{templatefile}\" does not exist")

            # use --start-group and --end-group because we're not sure of the ordering of the libs
            startgrp = " \"-Wl,--start-group\" "
            endgrp = " \"-Wl,--end-group\" "

            # add some additional system libraries that are sometimes needed but are not in the conan recipe (?)
            # TODO: make this list dynamic or move it outside of this generator
            # FIXME: check the "frameworks" and "system_libs" entries in the conan datastructure
            extralibslnx = " \"-lz\" \"-ldl\" "
            extralibsmac = " \"-lz\" \"-Wl,-framework,CoreFoundation\" \"-Wl,-framework,SystemConfiguration\" \"-Wl,-framework,Security\" "
            extralibswin = " \"-lz\" \"-lbcrypt\" \"-lcrypt32\" \"-lws2_32\" "

            # note: use '\n' for line terminator on all platforms
            if not package_requires_found:
                outf.write(f'package {outerlibname} requires :\n')
            if is_shared_lib:
                outf.write(f'  dynamic-libraries:\n')
                outf.write(f'    on-platform:\n')
                s = " ".join([fr'"{str(p).replace('\\', '/')}"' for p in libs["linux"]])
                outf.write(f'      linux: ( {s} )\n')
                s = " ".join([fr'"{str(p).replace('\\', '/')}"' for p in libs["macos"]])
                outf.write(f'      os-x: ( {s} )\n')
                s = " ".join([fr'"{str(p).replace('\\', '/')}"' for p in libs["windows"]])
                outf.write(f'      windows: ( {s} )\n')
            else:  # static
                pass
            outf.write(f'  ccflags:\n')
            outf.write(f'    on-platform:\n')
            incdirall = ""
            for incdir in include_dirs:
                incdirall += f" \"-I{incdir.replace('\\', '/')}\" "
            s = " ".join([fr'"{str(p).replace('\\', '/')}"' for p in libs["linux"]])
            outf.write(f'      linux: ( {incdirall} {startgrp} {s} {extralibslnx} {endgrp} )\n')
            s = " ".join([fr'"{str(p).replace('\\', '/')}"' for p in libs["macos"]])
            outf.write(f'      os-x: ( {incdirall} {s} {extralibsmac} )\n')
            s = " ".join([fr'"{str(p).replace('\\', '/')}"' for p in libs["windows"]])
            outf.write(f'      windows: ( {incdirall} {startgrp} {s} {extralibswin} {endgrp} )\n')

            outf.write(f'\n')

            if not package_tests_requires_found:
                outf.write(f'package {outerlibname}/tests requires :\n')
            if is_shared_lib:
                outf.write(f'  dynamic-libraries:\n')
                outf.write(f'    on-platform:\n')
                s = " ".join([fr'"{str(p).replace('\\', '/')}"' for p in libs["linux"]])
                outf.write(f'      linux: ( {s} )\n')
                s = " ".join([fr'"{str(p).replace('\\', '/')}"' for p in libs["macos"]])
                outf.write(f'      os-x: ( {s} )\n')
                s = " ".join([fr'"{str(p).replace('\\', '/')}"' for p in libs["windows"]])
                outf.write(f'      windows: ( {s} )\n')
            else:  # static
                pass
            outf.write(f'  ccflags:\n')
            outf.write(f'    on-platform:\n')
            s = " ".join([fr'"{str(p).replace('\\', '/')}"' for p in libs["linux"]])
            outf.write(f'      linux: ( {incdirall} {startgrp} {s} {extralibslnx} {endgrp} )\n')
            s = " ".join([fr'"{str(p).replace('\\', '/')}"' for p in libs["macos"]])
            outf.write(f'      os-x: ( {incdirall} {s} {extralibsmac} )\n')
            s = " ".join([fr'"{str(p).replace('\\', '/')}"' for p in libs["windows"]])
            outf.write(f'      windows: ( {incdirall} {startgrp} {s} {extralibswin} {endgrp} )\n')


    def get_component_libs_from_dependency(self, depname: str, depinst) -> list:
        #self._conanfile.output.trace(f"    - depinst.cppinfo: \"{depinst.cpp_info.serialize()}\"")
        #self._conanfile.output.trace(f"    - depinst.cppinfo:")
        #self._conanfile.output.trace(json.dumps(depinst.cpp_info.serialize(), jdkwargs={"indent": 2}))
        # collect required library definitions from dependencies
        self._conanfile.output.trace(f"    - components:")
        complist = []
        for compname, compinst in depinst.cpp_info.get_sorted_components().items():
            complist.append(self.get_libs_from_component(compname, compinst))

        #breakpoint()
        self._conanfile.output.trace(f"    - get_component_libs_from_dependency(\"{depname}\", inst) -> \"{complist}\"")
        return complist

    def write_cpp_info_to_fragment(self, is_shared_lib: bool, include_dirs: list[str], libs: dict[str, dict[str, Path]]):
        self._conanfile.output.trace(f"  > write_cpp_info_to_fragment({is_shared_lib}, \"{libs}\"")
        outerlibname = self._conanfile.name.removeprefix("slm-")
        relative_path = Path(f"{{.}}/../{outerlibname}/lib")

        # lfn["relative"]["linux"] = ["a", "b"]
        libfilenames: dict[str, dict[str, list[str]]] = {}
        for tp in ["full", "relative"]:
            libfilenames[tp] = {}
            for os in ["linux", "macos", "windows"]:
                libfilenames[tp][os] = []

        for pkgname, d in libs.items():
            # special case for openssl, order ssl first, then crypto
            if pkgname=='openssl' and 'crypto' in d and 'ssl' in d:
                # move 'crypto' to the end
                d['crypto'] = d.pop('crypto')

            for l, p in d.items():
                # calculate filenames
                if is_shared_lib:
                    flnx = f"lib{l}.so"
                    fmac = f"lib{l}.dylib"
                    fwin = f"lib{l}.dll"
                else:
                    flnx = f"lib{l}.a"
                    fmac = f"lib{l}.a"
                    fwin = f"lib{l}.a"

                libfilenames["full"]["linux"].append(Path(p[0]) / flnx)
                libfilenames["full"]["macos"].append(Path(p[0]) / fmac)
                libfilenames["full"]["windows"].append(Path(p[0]) / fwin)

                relative_path = Path(f"{{.}}/../{pkgname}/lib")
                libfilenames["relative"]["linux"].append(relative_path / flnx)
                libfilenames["relative"]["macos"].append(relative_path / fmac)
                libfilenames["relative"]["windows"].append(relative_path / fwin)

        # debug output filenames
        for os, td in libfilenames.items():
            for tp, a in td.items():
                self._conanfile.output.trace(f"  {tp}-{os}: {', '.join([str(p) for p in a])}")

        #breakpoint()
        
        # Write stanza.proj fragment with full library paths for dependencies in conan cache
        outfilename = f"stanza-{outerlibname}.proj"
        self._conanfile.output.trace(f"Generating {outfilename} for {outerlibname}")
        self.write_package_fragment(is_shared_lib, include_dirs, libfilenames["full"], outfilename)

        # Write stanza.proj fragment with relative library paths for dependencies in an slm package
        outfilename = f"stanza-{outerlibname}-relative.proj"
        self._conanfile.output.trace(f"Generating {outfilename} for {outerlibname}")
        self.write_package_fragment(is_shared_lib, [], libfilenames["relative"], outfilename)

    def dep_is_shared_lib(self, dep, dinst):
        # compare with a public interface string value instead of the private interface PackageType.SHARED
        shared_lib_string = 'shared-library'
        return str(dinst.package_type) == shared_lib_string

    def create_stanza_proj_fragment(self):
        incdirs = []
        libs = {}
        is_shared_lib = False
        for dep in self._conanfile.dependencies.items():
            dreq = dep[0]
            dinst = dep[1]
            depname = str(dreq.ref).partition('/')[0]
            self._conanfile.output.trace(f"")
            #self._conanfile.output.trace(f"  checking dep \"{dreq.serialize()}\"")
            self._conanfile.output.trace(f"  - dependency: {dreq.ref}")
            self._conanfile.output.trace(f"    - pref: {dinst.pref}")
            self._conanfile.output.trace(f"    - package_type: {dinst.package_type}")
            self._conanfile.output.trace(f"    - package_path: {dinst.package_path if dinst.package_folder else 'None'}")

            if not dreq.libs:
                self._conanfile.output.trace(f"    - dep \"{dreq.ref}\" has no libs, skipping")
                continue
            if len(dinst.cpp_info.components) > 0:
                self._conanfile.output.trace(f"    - dep \"{dreq.ref}\" components:")
                is_shared_lib = dinst.package_type is self.dep_is_shared_lib(dep, dinst)  # assumption: accept the last value because they should all be the same
                for compname, compinst in dinst.cpp_info.get_sorted_components().items():
                    incdirs.extend(compinst.includedirs)
                for cl in self.get_component_libs_from_dependency(str(dreq.ref), dinst):
                    self._conanfile.output.trace(f"    - dep \"{dreq.ref}\" component \"{cl}\"")
                    # cl is a dictionary {name: path}
                    if depname in libs:
                        libs[depname].update(cl)
                    else:
                        libs[depname] = cl
            else:
                self._conanfile.output.trace(f"    - dep \"{dreq.ref}\" include dirs: {dinst.cpp_info.includedirs}")
                self._conanfile.output.trace(f"    - dep \"{dreq.ref}\" lib dirs: {dinst.cpp_info.libdirs}")
                self._conanfile.output.trace(f"    - dep \"{dreq.ref}\" libs: {dinst.cpp_info.libs}")
                incdirs.extend(dinst.cpp_info.includedirs)
                if len(dinst.cpp_info.libdirs) > 1:
                    self._conanfile.output.error(f"Dependency \"{dreq.ref}\" has more than one libdir.  This generator currently doesn't handle that.")
                if len(dinst.cpp_info.libdirs) > 0:
                    is_shared_lib = dinst.package_type is self.dep_is_shared_lib(dep, dinst)  # assumption: accept the last value because they should all be the same
                    libdir = dinst.cpp_info.libdirs[0]
                    d = {}
                    for l in dinst.cpp_info.libs:
                        d[l] = [Path(libdir)]
                    # d is a dictionary {name: path}
                    if depname in libs:
                        libs[depname].update(d)
                    else:
                        libs[depname] = d
                # else no libdirs

            #breakpoint()

        self.write_cpp_info_to_fragment(is_shared_lib, incdirs, libs)

    def generate(self):
        self._conanfile.output.trace(f"---- LBStanzaGenerator version {LBStanzaGeneratorPyReq.version} .generate() ----")

        self.create_stanza_proj_fragment()

        self._conanfile.output.trace("----")
