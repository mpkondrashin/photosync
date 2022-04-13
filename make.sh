#!/bin/sh

python setup.py build_ext --inplace
cython --embed -o photo.c photo.py
gcc -v -Os -I/System/Library/Frameworks/Python.framework/Versions/2.7/include/python2.7 -L /System/Library/Frameworks/Python.framework/Versions/2.7/lib -o photo photo.c  -l python2.7 -lpthread -lm -lutil -ldl
