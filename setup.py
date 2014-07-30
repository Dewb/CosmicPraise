#!/usr/bin/env python

from setuptools import setup

#from distutils.core import setup
from pip.req import parse_requirements
install_reqs = parse_requirements("requirements.txt")
reqs = [str(ir.req) for ir in install_reqs]

sctk = {
    "name": "cosmic",
    "description": "Cosmic Praise client",
    "author":"Michael Dewberry et al.",
    "packages": ["CosmicPraise"],
    "package_dir": {"CosmicPraise": "client/python"},
    "py_modules":[
        "CosmicPraise.address_test",
        "CosmicPraise.color_utils",
        "CosmicPraise.opc",
        "CosmicPraise.__init__", 
    ],
    "version": "0.1",
    "scripts": ["simulator/osx-10.9/gl_server", "scripts/cosmicpraise.py"],
    "package_data": {"layout": "layout/*.json"},
    "install_requires": reqs,
}

if __name__ == "__main__":

    setup(**sctk)
