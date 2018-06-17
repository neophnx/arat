#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Sat Jun  9 18:02:50 2018

@author: phnx
"""

from setuptools import setup

setup(name='arat',
      version='0.0',
      description='Arat annotation tool',
      url='https://github.com/neophnx/arat/',
      author='neophnx',
      author_email='',
      license='MIT',
      packages=['.'],
      zip_safe=False,
      classifiers=[
        "Programming Language :: Python",
        "Development Status :: 1 - Planning",
        "License :: OSI Approved",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6"],
      install_requires=[i.strip() for i in open("requirements.txt").read().split("\n")]
      )