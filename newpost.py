#!/usr/bin/env python3

import sys
import now
import yaml
import getopt
import os

def usage(exitcode, program, message=""):

	# TODO: read the blog / project paths from the blog's config file

	if message:
		print(message)
	print(f"""\
Usage: {program} [-a/--author=<AUTHOR>] [-p/--project <TAG>] [-s/--sketch] [-A/--article] [-t/--tags=<TAG0>,<TAG1>,<TAG2>...<TAGN>] [-h/--help] <TITLE>
Where:
	--author specifies the author name
		defaults to "vigilante sculpting"
	--project specifies this as a project post, using the provided <TAG>
	--sketch specifies this as a sketch post
	--article specifies this as an article post
	--tags specifies a comma-separated tag list
	--help prints this help and exits
	TITLE is the title of the post

	If none of --article, --sketch or --project arguments are present, then the post is a blog post
	Only one of --article, --sketch or --project arguments can be present at once
""")
	sys.exit(exitcode)

author = "vigilante sculpting"
currently = now.now()
date = currently.strftime("%Y-%m-%dT%H:%M:%S %z")
projecttag = None
sketch = False
article = False
tags = None
thumbnail = ""

try:
	optlist, args = getopt.gnu_getopt(sys.argv[1:], 'a:p:sAt:h', ['author=', 'project=', 'sketch', 'article', 'tags=', 'help'])
except getopt.GetoptError as err:
	usage(-2, sys.argv[0], err)
for opt, arg in optlist:
	if opt in ('-a', '--author'):
		author = arg
	elif opt in ('-p', '--project'):
		projecttag = arg
	elif opt in ('-s', '--sketch'):
		sketch = True
	elif opt in ('-A', '--article'):
		article = True
	elif opt in ('-t', '--tags'):
		tags = arg.split(",")
	elif opt in ('-h', '--help'):
		usage(0, sys.argv[0], '')
	else:
		usage(-1, sys.argv[0], "unknown argument [%s]" % opt)
if len(args) == 0:
	usage(-1, sys.argv[0], "missing required TITLE argument")
elif len(args) > 1:
	usage(-1, sys.argv[0], "illegal arguments: %s" % (" ".join(args)))

title = args[0]

# slugify, ie. rather than replace known "bad" characters, have only good characters in the string, ie.
# replace anything that isn't a narrow subrange of ascii with underscores.
safetitle = title.lower().replace(" ", "_").replace("&", "_").replace("!", "_").replace(",", "_")

header = {
	'author': author,
	'date': date,
	'thumbnail': thumbnail,
	'title': title,
}
if tags is not None:
	header['tags'] = tags

if projecttag is not None:
	header['project'] = projecttag
	outputdir = "content/projects"
elif sketch:
	outputdir = "content/sketches"
elif article:
	outputdir = "content/articles"
else:
	outputdir = "content/blog"

output = yaml.dump(header)
template = f"""---
{output}

---
"""

filename = "%s-%s_local.md" % (currently.strftime("%Y-%m-%d"), safetitle)
filepath = os.path.join(outputdir, filename)

print(f"creating post [{filepath}]")

with open(filepath, "w") as f:
	f.write(template)

#TODO: do something like this here, so the file opens up in $EDITOR
# Also, create the file INSIDE THE BLOG, so we don't have to move it at all.

import sys, tempfile, os
from subprocess import call

EDITOR = os.environ.get('MDEDITOR','nano') #that easy!
call([EDITOR, filepath])

