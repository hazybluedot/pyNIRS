import ez_setup
ez_setup.use_setuptools()

from setuptools import setup

setup(
    name='pyNIRS',
    author='Darren Maczka',
    author_email='dmaczka@vt.edu',
    version='0.9',
    description='Utilities for working with NIRS data',
    packages=[ 'pyNIRS' ],
    scripts = [ 'bin/nirx2nirs.py' ],
    install_requires = [ 'numpy', 'scipy' ]
)
