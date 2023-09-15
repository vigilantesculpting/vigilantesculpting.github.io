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

import faeiry

### load the given markdown(!!!) file

filepath = sys.argv[1]
with open(filepath, "r") as f:
	text = f.read()

dirpath, filename = os.path.split(filepath)
basename, ext = os.path.splitext(filename)
basename = re.sub(r'_local$', '', basename)
outputfilepath = os.path.join(dirpath, basename + ext)
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

print(f"header: [{header}]")
print(f"body: [{body}]")

# is there a thumbnail in the header?
metadata = yaml.safe_load(header)
if metadata and "thumbnail" in metadata:
	thumbnailpath = metadata['thumbnail']
	print(f"thumbnailpath: [{thumbnailpath}]")
	# is the thumbnail a local (non-blog) url?
	if re.match(r'/Users', thumbnailpath):
		uploadables.append(thumbnailpath)

# now parse the body and detect all local images:

for m in re.finditer(r'\!\[.*?\]\((.*?)\)', body):
	print("match!")
	uploadables.append(m.group(1))

print(f"uploadables: {uploadables}")

### invoke faeiry to upload the images and collect the uploaded URLs, replace them in the document

def upload(uploadables, title):
	if len(uploadables) == 0:
		return []
	client = faeiry.authenticate()
	imagedata = faeiry.uploadimages(client, uploadables, title=title)
	uploadedimages = {}
	for localpath, data in zip(uploadables, imagedata):
		uploadedimages[localpath] = data['link']
	return uploadedimages

title = metadata["title"] if "title" in metadata else "unnamed"
uploadedimages = upload(uploadables, title)
print(f"uploadedimages: {uploadedimages}")

### replace the local image urls with the uploaded urls in the frontmatter and body

# replace the thumbnail (if any)

if metadata and "thumbnail" in metadata and metadata["thumbnail"] in uploadedimages:
	metadata["thumbnail"] = uploadedimages[metadata["thumbnail"]]

# replace the images in the body

def substitute_uploadable(m):
	return f"![{m.group(1)}]({uploadedimages[m.group(2)]})"

newbody, count = re.subn(r'\!\[(.*?)\]\((.*?)\)', substitute_uploadable, body)
print(f"newbody: {newbody}")

### write the file back to disk as md

newfile = f"""---
{yaml.dump(metadata) if metadata else ''}
---
{newbody}"""

print(f"newfile:\n{newfile}")

if 1:
	with open(outputfilepath, "w") as f:
		f.write(newfile)

	print("adding file to git")
	subprocess.run(["git", "add", outputfilepath], check=True)
	print("committing file to git")
	subprocess.run(["git", "commit", "-m", f"modify post {outputfilepath}"], check=True)

# TODO: optionally, create / update a local database of replacement urls, so that we can always
# reference the same images again without duplicate uploads





