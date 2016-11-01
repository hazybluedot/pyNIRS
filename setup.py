from setuptools import setup

setup(
    name='pyNIRS',
    author='Darren Maczka',
    author_email='dmaczka@vt.edu',
    version='0.9',
    packages=[ 'pyNIRS' ],
    scripts = [ 'bin/nirx2nirs' ],
    install_requires = [ 'numpy', 'scipy' ]
)
