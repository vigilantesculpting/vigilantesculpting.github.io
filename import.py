#!/usr/bin/env python3

""" This script takes in a markdown filepath.
It trolls the contents of the file, looking for local images.
It then uploads these images to imgur, and replaces the urls in the body of
the file with the newly uploaded urls.
The modified body is written back to the file.

It will then add and commit the modified file to the repo.
"""

import sys
import os
import re
import yaml
import subprocess
import getopt

import faeiry
from PIL import Image

def usage(msg = "", result = 0):
	if len(msg) > 0:
		print(msg)
	print(f"""Imports a local post into the contents. Can upload the images in the post to Imgur
Usage: {sys.argv[0]} [--dry-run/-n] [--import-only/-i] [--help/-h] INPUTPATH
Where
  --dry-run     : Do a dry run. Print out statistics, do not perform any import or uploads
  --import-only : Only import, do not upload
  --help        : Show this help
  INPUTPATH     : The path of the post to import
""", end='')
	sys.exit(result)

dryrun = False

opts, args = getopt.gnu_getopt(sys.argv[1:], "nh")
for opt, arg in opts:
	match opt:
		case "-n":
			dryrun = True
			print("Note: dry run!")
		case "-h":
			usage()

if len(args) != 1:
	usage("INPUTPATH is required!", 1)

### load the given markdown(!!!) file

filepath = args[0]
with open(filepath, "r") as f:
	text = f.read()

dirpath, filename = os.path.split(filepath)
pathparts = dirpath.split(os.sep)
outputfilepath = os.path.join("content", *pathparts[1:], filename)
print(f"inputfilepath:  {filepath}")
print(f"outputfilepath: {outputfilepath}")

### troll through the front matter and body & grab any local image references that need uploading to imgur

uploadables = []
uploadedimgs = {}

# split the frontmatter and body text
def splitheader(text):
	header, body = "", text # default is no header
	parts = re.split("---\n", text)
	if len(parts) > 1:
		if len(parts[0]) == 0 and len(parts) == 3:
			header, body = parts[1:]
	return header, body

header, body = splitheader(text)

#print(f"header: [{header}]")
#print(f"body: [{body}]")

# is there a thumbnail in the header?
metadata = yaml.safe_load(header)
if metadata and "thumbnail" in metadata:
	thumbnailpath = metadata['thumbnail']
	#print(f"thumbnailpath: [{thumbnailpath}]")
	# is the thumbnail a local (non-blog) url?
	if re.match(r'/Users', thumbnailpath):
		uploadables.append(thumbnailpath)

# now parse the body and detect all local images:

for m in re.finditer(r'\!\[.*?\]\((.*?)\)', body):
	filepath = m.group(1)
	uploadables.append(filepath)

print(f"uploadables: {uploadables}")

# sanity check: are these (a) images and (b) not larger than the maximum size
for imagepath in uploadables:
	imagepath = imagepath.replace('\\', '')
	img = Image.open(imagepath)
	if img.width > 1920 or img.height > 1920:
		raise Exception(f"Fail: Image {imagepath} is larger than 1920x1920")

### invoke faeiry to upload the images and collect the uploaded URLs, replace them in the document

def upload(uploadables, title):
	if len(uploadables) == 0:
		return []
	client = faeiry.authenticate()
	imagepaths = [imagepath.replace('\\', '') for imagepath in uploadables]
	imagedata = faeiry.uploadimages(client, imagepaths, title=title)
	uploadedimages = {}
	for localpath, data in zip(uploadables, imagedata):
		uploadedimages[localpath] = data['link']
	return uploadedimages

title = metadata["title"] if "title" in metadata else "unnamed"
if not dryrun:
	uploadedimages = upload(uploadables, title)
else:
	uploadedimages = {}
	for localpath in uploadables:
		uploadedimages[localpath] = localpath.replace('\\', '')
	print("dry run, images not uploaded!")

print(f"uploadedimages:")
for local, remote in uploadedimages.items():
	print(f"\t{local} -> {remote}")

### replace the local image urls with the uploaded urls in the frontmatter and body

# replace the thumbnail (if any)
if metadata and "thumbnail" in metadata and metadata["thumbnail"] in uploadedimages:
	metadata["thumbnail"] = uploadedimages[metadata["thumbnail"]]

# replace the images in the body

def substitute_uploadable(m):
	return f"![{m.group(1)}]({uploadedimages[m.group(2)]})"

newbody, count = re.subn(r'\!\[(.*?)\]\((.*?)\)', substitute_uploadable, body)

#print(f"newbody: {newbody}")

### write the file back to disk as md

newfile = f"""---
{yaml.dump(metadata) if metadata else ''}
---
{newbody}"""

print(f"newfile:\n{newfile}")

if not dryrun:
	with open(outputfilepath, "w") as f:
		f.write(newfile)

	print("adding file to git")
	subprocess.run(["git", "add", outputfilepath], check=True)
	print("committing file to git")
	subprocess.run(["git", "commit", "-m", f"modify post {outputfilepath}"], check=True)

# TODO: optionally, create / update a local database of replacement urls, so that we can always
# reference the same images again without duplicate uploads





