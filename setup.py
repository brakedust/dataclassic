"""
Setup script for doit
"""

from setuptools import setup, find_packages
import os.path as osp
import shutil
import sys
import os
import subprocess

parent_path = osp.dirname(osp.abspath(__file__))

pkg_name = "koala"
import version_maker  # THIS NEEDS TO BE HERE

shutil.copyfile(
    osp.join(parent_path, pkg_name, "version.py"), osp.join(parent_path, "version.py")
)
from version import VERSION

my_classifiers = [
    # How mature is this project? Common values are
    #   3 - Alpha
    #   4 - Beta
    #   5 - Production/Stable
    "Development Status :: 5 - Production/Stable",
    # Indicate who your project is intended for
    "Intended Audience :: Developers",
    "Topic :: Development",
    # Pick your license as you wish (should match "license" above)
    #'License :: OSI Approved :: MIT License',
    # Specify the Python versions you support here. In particular, ensure
    # that you indicate whether you support Python 2, Python 3 or both.
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.7",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
]


# if "docs" in sys.argv:

#     os.chdir(parent_path)
#     subprocess.call(r"python cli_doc.py".split(" "))
#     os.chdir(parent_path)
#     subprocess.call(r"sphinx-apidoc --force doit -o docs/source/doit".split(" "))
#     os.chdir(parent_path)
#     subprocess.call(
#         r"sphinx-apidoc --force doit_tests -o docs/source/doit_tests".split(" ")
#     )
#     os.chdir("docs")
#     if sys.platform == "win32":
#         subprocess.call(".\make.bat html".split(" "))
#     else:
#         subprocess.call("make -f Makefile html".split(" "))

#     os.chdir(parent_path)
#     if os.path.exists("doit/docs"):
#         shutil.rmtree("doit/docs")
#         import time

#         time.sleep(1)

#     if os.path.exists("docs/build/html"):
#         shutil.copytree("docs/build/html", "doit/docs")
#     else:
#         print("Error building documention!!!!!!!!!")
#         sys.exit(1)

#     sys.argv.remove("docs")


# if "test" in sys.argv:
#     if sys.platform == "win32":
#         subprocess.call("py.test.exe -v --cov=doit doit_tests".split(" "))
#     else:
#         subprocess.call("py.test -v --cov=doit doit_tests".split(" "))

#     sys.argv.remove("test")


# if len(sys.argv) == 1:
#     sys.exit()


my_packages = find_packages("koala")
# my_packages.append("{0}.plugins".format(pkg_name))


setup(
    name=pkg_name,
    description="",
    author="",
    author_email="",
    url="/dev/null",
    packages=my_packages,
    include_package_data=True,
    classifiers=my_classifiers,
    keywords="",
    install_requires=[],
    # entry_points={"console_scripts": ["{0} = {0}.application:main".format(pkg_name)]},
    # package_data={"{0}/doc".format(pkg_name): ["*"]},
    version=VERSION,
)
