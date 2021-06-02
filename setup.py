#!/usr/bin/env python

from setuptools import setup

from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(name='tock',
      version='0.25',
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
        'Programming Language :: Python :: 3',
        ],
      packages=['tock'],
      python_requires='>=3.7',
      install_requires=['openpyxl'],
      long_description=long_description,
      long_description_content_type='text/markdown',
      )
