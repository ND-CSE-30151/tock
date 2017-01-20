#!/usr/bin/env python

from setuptools import setup

setup(name='tock',
      version='0.14',
      description='Theory of Computing Toolkit',
      author='David Chiang',
      author_email='dchiang@nd.edu',
      url='https://github.org/ND-CSE-30151/tock',
      license='MIT',
      classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Education',
        'Topic :: Education',
        'Topic :: Scientific/Engineering :: Mathematics',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        ],
      packages=['tock'],
      install_requires=['six', 'openpyxl'],
      )
