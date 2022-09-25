from setuptools import Extension, find_packages, setup
from Cython.Build import cythonize
#import numpy

modules=[
#    Extension("ILI9341",  ["ILI9341/ILI9341.py"], include_dirs=[numpy.get_include()]), 
    Extension("ILI9341",  ["ILI9341/ILI9341.py"]), 
]


setup(
    name="ILI9341",
    
    # Project Version
    version="1.0", 
    
    # Detailed description of your package
    description="Modified version of Adafruids archvived ILI9341 library with multiple extensions/adjustments",
    license="MIT",
    url="https://github.com/mk-81/ILI9341",

    # Dependencies/Other modules required for your package to work
    install_requires=["numpy", "RPi.GPIO"],

    ext_modules=cythonize(
                    modules,
                    compiler_directives={
                        "language_level":3
                    }
                ),
    packages=find_packages(),
    zip_safe=True,

    keywords=["ILI9341"]
)