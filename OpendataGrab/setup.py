#!/usr/bin/python
# -*- coding: utf-8 -*-

from setuptools import setup

_vmaj = 0
_vmin = 1
setup (name="opendata",
        version="%d.%d" % (_vmaj, _vmin),
        description="",
        author="DWD/amaul",
        author_email="alexander.maul@dwd.de",
        url="https://opendata.dwd.de",
        long_description="",
        license="GNU GPL V.3",
        entry_points={ "console_scripts": ["odgrab = opendata.grab:run"] },
        classifiers=["Programming Language :: Python :: 2 :: Only"],
        packages=["opendata"],
        package_dir={"opendata": "opendata"},
        install_requires=["argparse", "requests", "bz2", "logging"],
        )
