#!/usr/bin/env bash

BASEDIR=$(dirname "$0")

$BASEDIR/import.py /Volumes/EOS_DIGITAL ~/Pictures/photo/digital

hdiutil detach /Volumes/EOS_DIGITAL