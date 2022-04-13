#!/usr/bin/env bash

[ $# -eq 2 ] || exec echo "Usage $0 <disk> <number>"

VECTOR="photo/Software/all0${2}.dmg"
./sync_dmg.py ~/Pictures/$VECTOR /Volumes/$1/$VECTOR

