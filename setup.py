#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Sat Jun  9 18:02:50 2018

@author: phnx
"""

from setuptools import setup

setup(name='brat',
      version='latest',
      description='Brat annotation tool',
      url='https://github.com/neophnx/brat/',
      author='Brat contributors',
      author_email='',
      license='GPLv3',
      packages=['server'],
      zip_safe=False,
      classifiers=[
        "Programming Language :: Python",
        "Development Status :: 1 - Planning",
        "License :: OSI Approved",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6"],
      install_requires=["six"]
      )