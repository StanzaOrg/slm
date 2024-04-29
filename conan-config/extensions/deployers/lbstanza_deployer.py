
# Conan L.B.Stanza Deployer
# https://docs.conan.io/2/reference/extensions/deployers.html
# https://docs.conan.io/2/examples/extensions/deployers/sources/custom_deployer_sources.html

from shutil import copytree
#from conans.errors import ConanException
from pathlib import Path
import os

# lbstanza_deployer function
def deploy(graph, output_folder: str, **kwargs):
    graph.root.conanfile.output.trace("---- lbstanza_deployer deploy() ----")

    # for each dependency
    for name, dep in graph.root.conanfile.dependencies.items():
        # copy files to this directory
        outdir = Path(output_folder)/'deps'

        # if the dependency is a library
        if (dep.package_type=='static-library' or dep.package_type=='shared-library'
                or dep.package_type=='header-library') and (dep.package_path).exists():
            incsrc = dep.package_path/'include'
            incdst = outdir/'include'
            libsrc = dep.package_path/'lib'
            libdst = outdir/'lib'
            if incsrc.exists():
                incdst.mkdir(parents=True, exist_ok=True)
                graph.root.conanfile.output.trace(f"  copying dependency include directory {incsrc} to {incdst}")
                copytree(incsrc, incdst, dirs_exist_ok=True)
            if libsrc.exists():
                libdst.mkdir(parents=True, exist_ok=True)
                graph.root.conanfile.output.trace(f"  copying dependency lib directory {libsrc} to {libdst}")
                copytree(libsrc, libdst, dirs_exist_ok=True)
