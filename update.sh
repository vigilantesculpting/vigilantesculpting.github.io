#!/bin/bash
set -euvx

git pull --rebase && ./main.py && git add -u :/ && git add docs && git commit -m "rebuild"
# git push origin HEAD




