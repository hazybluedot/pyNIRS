# pyNIRS

This project will contain data processing and analysis scripts to work with fNIRS data. It is heavily modeled after existing Matlab scripts available from [NITRC].

Currently, the only utility implemented is one to convert the raw data
produced by the NIRx machine to a file format that the [Homer2] package
can use. Over time, I will port over filtering and processing capabilities currently provided by [Homer2] into a native-python implementation.

[NITRC]: https://www.nitrc.org/
[Homer2]: https://www.nitrc.org/projects/homer2

## Dependencies

This package uses both [numpy] and [scipy]

[numpy]: http://www.numpy.org/
[scipy]: https://www.scipy.org/

## Installation

~~~~
$ pip install .
$ python setup.py install
~~~~

Note that the `pip` command is a work-around for an issue with the interaction of setuptools, scipy and numpy

## Usage

This is currently a command line only application (I may eventually write a GUI wrapper, certainly feel free to contribute one sooner :-) )

~~~~
$ nirx2nirs path/to/NIRS-xxxx.hdr
~~~~

For more detailed usage instruction

~~~~
$ nirx2nirs -h
~~~~

Note that on windows the setup step should create a `.exe` file in your path. You may have to include that extension when running commands from the commmand line. I have not tested on Windows yet.
