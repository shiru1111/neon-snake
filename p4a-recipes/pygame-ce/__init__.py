from os.path import join
from pythonforandroid.recipe import CompiledComponentsPythonRecipe
from pythonforandroid.toolchain import current_directory


class PygameCeRecipe(CompiledComponentsPythonRecipe):
    """
    Recipe to build apps based on SDL2-based pygame-ce.
    """

    version = '2.4.0'
    url = 'https://github.com/pygame-community/pygame-ce/archive/{version}.tar.gz'

    site_packages_name = 'pygame'
    name = 'pygame-ce'

    depends = ['python3', 'sdl2', 'sdl2_image', 'sdl2_mixer', 'sdl2_ttf', 'setuptools']
    call_hostpython_via_targetpython = False
    install_in_hostpython = False

    def prebuild_arch(self, arch):
        super().prebuild_arch(arch)
        with current_directory(self.get_build_dir(arch.arch)):
            setup_template = open(join("buildconfig", "Setup.Android.SDL2.in")).read()
            env = self.get_recipe_env(arch)
            env['ANDROID_ROOT'] = join(self.ctx.ndk.sysroot, 'usr')

            bootstrap_jni = join(self.ctx.bootstrap.build_dir, 'jni')
            libs_dir = join(self.ctx.bootstrap.build_dir, "libs", str(arch))

            sdl_includes = (
                f" -I{join(bootstrap_jni, 'SDL')}"
                f" -I{join(bootstrap_jni, 'SDL', 'include')}"
                f" -I{join(bootstrap_jni, 'SDL', 'include', 'SDL2')}"
                f" -I{join(bootstrap_jni, 'SDL2')}"
                f" -I{join(bootstrap_jni, 'SDL2', 'include')}"
                f" -L{libs_dir}"
            )

            sdl_image_includes = (
                f"-I{join(bootstrap_jni, 'SDL2_image')}"
                f" -I{join(bootstrap_jni, 'SDL2_image', 'include')}"
                f" -I{join(bootstrap_jni, 'SDL2_image', 'include', 'SDL2')}"
            )

            sdl_ttf_includes = (
                f"-I{join(bootstrap_jni, 'SDL2_ttf')}"
                f" -I{join(bootstrap_jni, 'SDL2_ttf', 'include')}"
                f" -I{join(bootstrap_jni, 'SDL2_ttf', 'include', 'SDL2')}"
            )

            sdl_mixer_includes = (
                f"-I{join(bootstrap_jni, 'SDL2_mixer')}"
                f" -I{join(bootstrap_jni, 'SDL2_mixer', 'include')}"
                f" -I{join(bootstrap_jni, 'SDL2_mixer', 'include', 'SDL2')}"
            )

            setup_file = setup_template.format(
                sdl_includes=sdl_includes,
                sdl_ttf_includes=sdl_ttf_includes,
                sdl_image_includes=sdl_image_includes,
                sdl_mixer_includes=sdl_mixer_includes,
                jpeg_includes="",
                png_includes="",
                freetype_includes=""
            )

            # Disable optional imageext module since Neon Snake is 100% procedural
            # and does not load external image files. This completely prevents any
            # missing header issues with image libraries.
            setup_file = setup_file.replace(
                "imageext src_c/imageext.c $(SDL) $(IMAGE) $(DEBUG)",
                "# imageext src_c/imageext.c $(SDL) $(IMAGE) $(DEBUG)"
            )

            open("Setup", "w").write(setup_file)

    def get_recipe_env(self, arch):
        env = super().get_recipe_env(arch)
        env['USE_SDL2'] = '1'
        env["PYGAME_CROSS_COMPILE"] = "TRUE"
        env["PYGAME_ANDROID"] = "TRUE"
        return env


recipe = PygameCeRecipe()
