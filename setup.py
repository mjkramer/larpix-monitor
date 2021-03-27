#!/usr/bin/env python

from distutils.core import setup

setup(name='larpix-monitor',
      version='0.0',
      description='A data-quality monitor for LArPix',
      author='Peter Madigan',
      author_email='pmadigan@berkeley.edu',
      packages=['monitor'],
      scripts=['run_monitor.py'],
      requires=[
        'numpy',
        'matplotlib',
        'larpix_control'
      ]
     )
