import os
from conan import ConanFile
from conan.tools.build import can_run


class slmTestConan(ConanFile):
    settings = "os", "compiler", "build_type", "arch"

    def requirements(self):
        self.requires(self.tested_reference_str)

    def test(self):
        if can_run(self):
            SLM_FOLDER = os.environ["SLM_ROOT_DIR"]
            self.run(f"{SLM_FOLDER}/slm version", env="conanrun")
