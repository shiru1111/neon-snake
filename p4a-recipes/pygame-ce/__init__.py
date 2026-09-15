import os
from os.path import join, isdir
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

    depends = ['sdl2', 'sdl2_image', 'sdl2_mixer', 'sdl2_ttf', 'setuptools', 'jpeg', 'png']
    call_hostpython_via_targetpython = False
    install_in_hostpython = False

    def prebuild_arch(self, arch):
        super().prebuild_arch(arch)
        with current_directory(self.get_build_dir(arch.arch)):
            setup_template = open(join("buildconfig", "Setup.Android.SDL2.in")).read()
            env = self.get_recipe_env(arch)
            env['ANDROID_ROOT'] = join(self.ctx.ndk.sysroot, 'usr')

            png = self.get_recipe('png', self.ctx)
            png_lib_dir = join(png.get_build_dir(arch.arch), '.libs')
            png_inc_dir = png.get_build_dir(arch.arch) if hasattr(png, 'get_build_dir') else ""

            jpeg = self.get_recipe('jpeg', self.ctx)
            jpeg_inc_dir = jpeg_lib_dir = jpeg.get_build_dir(arch.arch) if hasattr(jpeg, 'get_build_dir') else ""

            # Base directories
            bootstrap_jni = join(self.ctx.bootstrap.build_dir, 'jni')

            sdl_dirs = [
                join(bootstrap_jni, 'SDL'),
                join(bootstrap_jni, 'SDL', 'include'),
                join(bootstrap_jni, 'SDL', 'include', 'SDL2'),
                join(bootstrap_jni, 'SDL2'),
                join(bootstrap_jni, 'SDL2', 'include'),
                join(bootstrap_jni, 'SDL2', 'include', 'SDL2'),
            ]
            sdl_image_dirs = [
                join(bootstrap_jni, 'SDL2_image'),
                join(bootstrap_jni, 'SDL2_image', 'include'),
                join(bootstrap_jni, 'SDL2_image', 'include', 'SDL2'),
            ]
            sdl_ttf_dirs = [
                join(bootstrap_jni, 'SDL2_ttf'),
                join(bootstrap_jni, 'SDL2_ttf', 'include'),
                join(bootstrap_jni, 'SDL2_ttf', 'include', 'SDL2'),
            ]
            sdl_mixer_dirs = [
                join(bootstrap_jni, 'SDL2_mixer'),
                join(bootstrap_jni, 'SDL2_mixer', 'include'),
                join(bootstrap_jni, 'SDL2_mixer', 'include', 'SDL2'),
            ]

            # Collect include dirs from recipes if available
            for r_name, d_list in [
                ('sdl2', sdl_dirs),
                ('sdl2_image', sdl_image_dirs),
                ('sdl2_ttf', sdl_ttf_dirs),
                ('sdl2_mixer', sdl_mixer_dirs),
            ]:
                try:
                    r = self.get_recipe(r_name, self.ctx)
                    if hasattr(r, 'get_include_dirs'):
                        d_list.extend(r.get_include_dirs(arch))
                    if hasattr(r, 'get_build_dir'):
                        b = r.get_build_dir(arch.arch)
                        d_list.extend([b, join(b, 'include'), join(b, 'include', 'SDL2')])
                except Exception:
                    pass

            # Recursively find any folder containing header files in bootstrap build dir
            for search_path in [bootstrap_jni, getattr(self.ctx, 'build_dir', None)]:
                if search_path and isdir(search_path):
                    for root, dirs, files in os.walk(search_path):
                        if 'SDL_image.h' in files:
                            sdl_image_dirs.append(root)
                        if 'SDL_ttf.h' in files:
                            sdl_ttf_dirs.append(root)
                        if 'SDL_mixer.h' in files:
                            sdl_mixer_dirs.append(root)
                        if 'SDL.h' in files:
                            sdl_dirs.append(root)

            # Deduplicate and format include flags
            sdl_inc_flags = " ".join(f"-I{d}" for d in sorted(set(sdl_dirs)) if d and isdir(d))
            sdl_image_includes = " ".join(f"-I{d}" for d in sorted(set(sdl_image_dirs)) if d and isdir(d))
            sdl_ttf_includes = " ".join(f"-I{d}" for d in sorted(set(sdl_ttf_dirs)) if d and isdir(d))
            sdl_mixer_includes = " ".join(f"-I{d}" for d in sorted(set(sdl_mixer_dirs)) if d and isdir(d))

            # Extra library paths
            extra_libs = ""
            if hasattr(arch, 'ndk_lib_dir_versioned') and arch.ndk_lib_dir_versioned:
                extra_libs += f" -L{arch.ndk_lib_dir_versioned}"

            setup_file = setup_template.format(
                sdl_includes=(
                    f" {sdl_inc_flags}"
                    f" -L{join(self.ctx.bootstrap.build_dir, 'libs', str(arch))}"
                    f" -L{png_lib_dir} -L{jpeg_lib_dir}{extra_libs}"
                ),
                sdl_ttf_includes=sdl_ttf_includes,
                sdl_image_includes=sdl_image_includes,
                sdl_mixer_includes=sdl_mixer_includes,
                jpeg_includes=f"-I{jpeg_inc_dir}" if jpeg_inc_dir else "",
                png_includes=f"-I{png_inc_dir}" if png_inc_dir else "",
                freetype_includes=""
            )
            open("Setup", "w").write(setup_file)

    def get_recipe_env(self, arch):
        env = super().get_recipe_env(arch)
        env['USE_SDL2'] = '1'
        env["PYGAME_CROSS_COMPILE"] = "TRUE"
        env["PYGAME_ANDROID"] = "TRUE"
        return env


recipe = PygameCeRecipe()
