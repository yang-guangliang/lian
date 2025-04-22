#!/usr/bin/env python3

import os,sys

from setuptools import setup, find_packages

setup(
    name='lian',
    version='0.1',
    author = "Guangliang Yang",
    author_email = "yanggl@fudan.edu.cn",
    description = ("A general code analysis platform born for security analysis and AI systems"),
    license = "Apache 2.0",
    keywords = "program code security analysis AI",
    url = "https://gitee.com/fdu-ssr/lian",
    package_dir={'': 'src'},
    packages=find_packages(where='src'),
    entry_points={
        'console_scripts': [
            'lian=lian.interfaces.main:main'
        ],
    }
)
