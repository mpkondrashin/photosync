from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext

ext_modules = [ Extension("conf",       ["conf.py"]),
                Extension("entity",     ["entity.py"]),
                Extension("exif",       ["exif.py"]),
                Extension("hashmd5",    ["hashmd5.py"]),
                Extension("path",       ["path.py"]),
                Extension("photo",      ["photo.py"]),
                Extension("preview",    ["preview.py"]),
                Extension("progress",   ["progress.py"]),
                Extension("show",       ["show.py"]),
                Extension("util",       ["util.py"])
                ]


setup(
    name='PhotoSync',
    cmdclass={'build_ext': build_ext},
    ext_modules=ext_modules
)
