**This project is frozen and not expected to be updated.**

This is a script written to compile PDF and DjVu from image files with
scanned lecture notes.

Its main features are:
* automatic cropping and rotation of the input images
* ability to include Table of Contents in the generated files
* support for incremental builds
* ability to do its work in parallel on several processor cores

For stable versions see [releases](https://github.com/atrosinenko/lecture-notes-compiler/releases) page.
For the installation instruction, documentation, etc. please see the
`doc/` subdirectory.

**Important note:** This script uses multiple CPU cores at about 100%
for significant time so please check your cooling. Please note that
even if you disable multithreading in the configuration, some of
invoked utilities may automatically use all CPU cores.
It may use disks actively as well to eliminate multiple lossy compressions.
