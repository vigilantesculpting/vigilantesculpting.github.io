#!/bin/bash
set -euvx

# clean docs directory
rm -rf docs && git checkout docs
# rebase any upstream changes
git pull --rebase
# create the site
./main.py
# add all modified files
git add -u :/ 
# add the entire new docs directory
git add docs
# commit everything
git commit -m "rebuild"

# git push origin HEAD




