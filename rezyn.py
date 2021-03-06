#!/usr/bin/env python

"""Rezyn is a static website generator in Python
"""

# default
import sys
import os
import re
import shutil
import math
import getopt
import subprocess
import random
import errno    
import hashlib

# requirements
import datetime
import dateutil.parser
import lxml.html
import lxml.etree
import yaml
import markdown
import bbcode
import pytz

# local copy
import minifycss
import rjsmin

# library code
import nsdict
import solon

# Internal debugging / tracing
LOG = False
def log(*args, **kwargs):
	if LOG:
		for arg in args:
			sys.stderr.write(str(arg))
		sys.stderr.write("\n")

solon.LOG=False
#####################################################

def setlog(level):
	if level > 0:
		global LOG
		LOG = True
	solon.setlog(level - 1)

def readfile(filename):
	with open(filename, "r") as f:
		return f.read()

def writefile(filename, contents):
	with open(filename, "w") as f:
		f.write(contents)

def mkdir(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

def parsedate(date_str):
	d = dateutil.parser.parse(date_str)
	return d.strftime('%Y/%m/%d %H:%M:%S')

def splitlines(linelist, separator):
	# splits a list of lines into sublists, separated by the given separator
	indices = (i for i, value in enumerate(linelist) if value.startswith(separator))
	a = 0
	for i in indices:
		yield linelist[a:i]
		a = i+1
	yield linelist[a:]

def splitcontent(content, separator):
	# splits a piece of text into chunks separated by lines starting with the separator
	lines = content.split("\n")
	for chunks in splitlines(lines, separator):
		yield "\n".join(chunks)

def splitheader(content):
	parts = list(splitcontent(content, '---'))
	# a file with a valid yaml header should have multiple parts, and the length of the 
	# first part will be zero (ie. the first line will be '---')
	if len(parts) > 2 and len(parts[0]) == 0:
		return parts[1], "---".join(parts[2:])
	else:
		return "", "---".join(parts)

#####################################################

class Rezyn:

	def __init__(self, config):
		self.solon = solon.Solon(config)
		self.bbparser = bbcode.Parser()

	def parsebb(self, text):
		parser = bbcode.Parser()
		return parser.format(text)

	def parsemd(self, text):
		return markdown.markdown(text)

	def texttohtml(self, ext, text):
		# convert the body text into an html snippet, if it not an html file
		if ext == '.md':
			html = self.parsemd(text)
		elif ext == ".bb":
			html = self.parsebb(text)
		elif ext == ".html":
			html = text
		else:
			raise NoConversion("Do not know how to turn [%s] into HTML" % ext)
		return html

	def readfile(self, filename):
		"""Read content and metadata from file into a dictionary."""

		# Each file has a slug, which is pretty much its basename
		path, ext = os.path.splitext(filename)
		dirpath, base = os.path.split(path)
		slug = base
		content = nsdict.NSDict({
			'slug': slug,
		})

		# Read file content.
		filecontent = unicode(readfile(filename), encoding='utf-8')

		# split the yaml frontmatter and body text
		fileheader, filebody = splitheader(filecontent)
		fm = yaml.safe_load(fileheader)
		if fm is not None:
			# it is not an error if no yaml is present, the file simply has no metadata
			content.update(fm)

		# convert the body text into an html snippet, if it not an html file
		text = self.texttohtml(ext.lower(), filebody)

		# create an xml representation of the document
		# we have to add a root element, since the text may or may not have one
		root = lxml.html.fromstring("<div class='filecontent'>" + text + "</div>")

		# find all images, and prepare them for lightbox
		imgs = root.findall(".//img")
		if 'thumbnail' not in content and len(imgs) > 0:
			# if thumbnail was not set, and we have images, set it to the first image
			content['thumbnail'] = imgs[0].attrib["src"]

		# convert the html tree back to text
		text = lxml.html.tostring(root)
		content['content'] = text

		# convert the string date into a raw datetime we can work with
		if 'date' in content:
			datestr = content['date']
			content['date'] = dateutil.parser.parse(datestr)

		# escape any html entitied in the title here:
		#content['title'] = xml.sax.saxutils.escape(content['title'])

		return content

	def readcontent(self, contentpath):
		contentpath = os.path.join(self.solon.context.config.srcdir, contentpath)
		log("loading content from [%s]" % contentpath)
		# load everything in the path into env
		for dirName, subdirList, fileList in os.walk(contentpath):
			root = dirName[len(contentpath)+1:]
			for fileName in fileList:
				if fileName == ".DS_Store":
					continue
				fullpath = os.path.join(dirName, fileName)
				if 1:
					base, ext = os.path.splitext(fileName)
					var = os.path.join("content", root, base)
				else:
					var = os.path.join("content", root, fileName)
				log("adding content ", var)
				filecontent = self.readfile(fullpath)
				if self.solon.context['config/publish_all'] or "nopublish" not in filecontent:
					log("readcontent: adding content to [%s]" % var)
					self.solon.context[var] = filecontent

	def readtemplates(self, templatepath, depth = None):
		templatepath = os.path.join(self.solon.context.config.srcdir, templatepath)
		# load everything in the template folder
		for level, (dirName, subdirList, fileList) in enumerate(os.walk(templatepath)):
			root = dirName[len(templatepath)+1:]
			for fileName in fileList:
				fullpath = os.path.join(dirName, fileName)
				var = os.path.join("template", root, fileName)
				log("adding template ", var)
				self.solon.addtemplate(var, readfile(fullpath))
			if depth is not None and level == depth:
				break

	########################
	## checksums ###########

	def renamefileswithchecksums(self, targetdir):
		# split a path into its component parts
		def splitpath(path):
			parts = []
			a = path
			while a:
				a, b = os.path.split(a)
				if b:
					parts.append(b)
			parts.reverse()
			return parts
		log("renamefileswithchecksums in [%s]" % targetdir)
		targetparts = splitpath(targetdir)
		filekeys = {}
		for dirname, subdirs, filenames in os.walk(targetdir):
			for filename in filenames:
				filepath = os.path.join(dirname, filename)
				base, ext = os.path.splitext(filename)
				if ext.lower() in ('.css', '.js'):
					checksum = hashlib.md5(open(filepath,'rb').read()).hexdigest()
					newbase = base + '-' + checksum
					newfilename = newbase + ext
					# create the key out of the filepath, but without the leading components of the targetdir
					key = os.path.join(*splitpath(filepath)[len(targetparts):])
					# the key translates into the renamed filename
					filekeys[key] = newfilename
					newfilepath = os.path.join(dirname, newfilename)
					shutil.move(filepath, newfilepath)
					log("renaming file [%s] to [%s], key [%s]" % (filepath, newfilepath, key))
		return filekeys

	########################
	## minify ##############

	def minifydir(self, path):

		for dirName, subdirList, fileList in os.walk(path):
			for fileName in fileList:
				if fileName == ".DS_Store":
					continue
				base, ext = os.path.splitext(fileName)
				filename = os.path.join(dirName, fileName)
				if ext.lower() == ".css":
					mincss = minifycss.minify(readfile(filename))
					log("minifying css [%s]" % filename)
					writefile(filename, mincss)
				elif ext.lower() == ".js":
					minjs = rjsmin._make_jsmin(python_only = True)(readfile(filename))
					log("minifying js [%s]" % filename)
					writefile(filename, minjs)

	########################
	## output ##############

	def writeoutput(self):
		for filename, content in self.solon.context.output.dict().iteritems():
			path = os.path.join(self.solon.context['config/tgtdir'], self.solon.context['config/tgtsubdir'], filename)
			dirpath, filepath = os.path.split(path)
			mkdir(dirpath)
			log("writing [%s]..." % path)
			writefile(path, content)


	def setup(self):

		# set up timezone
		tz = pytz.timezone(self.solon.context['config/timezone'])
		self.solon.context['config/tz'] = tz
		self.solon.context['config/now'] = datetime.datetime.now(tz)
		self.solon.context['config/current_year'] = self.solon.context['config/now'].year

		targetdir = os.path.join(self.solon.context.config.tgtdir, self.solon.context.config.tgtsubdir)
		staticdir = os.path.join(self.solon.context.config.srcdir, self.solon.context.config.staticdir)
		log("setup sourcedir [%s] -> targetdir [%s]" % (staticdir, targetdir))

		# remove the target directory
		log("removing targetdir [%s]" % targetdir)
		try:
			#if os.path.exists(targetdir):
			#	
			shutil.rmtree(targetdir)
		except Exception as e:
			print "Exception:", e
			pass

		# copy everything from static to the target directory
		log("copy sourcedir [%s] to targetdir [%s]" % (staticdir, targetdir))
		shutil.copytree(staticdir, targetdir)
		if not ("config/debug" in self.solon.context and self.solon.context["config/debug"]):
			# web minify (css and js)
			log("minify web in targtdir [%s]" % targetdir)
			self.minifydir(targetdir)

		# rename each css/js file with its checksum key
		filekeys = self.renamefileswithchecksums(targetdir)
		# make the renamed files available to the template(s)
		self.solon.context['filekeys'] = filekeys

	def process(self):

		setlog(self.solon.context['config/verbose'])

		self.setup()

		#### Read in website content + templates

		self.readcontent(self.solon.context["config/contentdir"])
		self.readtemplates(self.solon.context["config/templatedir"])

		# post process the data

		posts = [self.solon.context['content/blog'][post] for post in self.solon.context['content/blog'].keys()]
		sortedposts = sorted(posts, key=lambda values: values['date'], reverse=True)
		self.solon.context['content/sortedposts'] = sortedposts

		# render the templates

		self.solon.rendertemplate("template/site.tpl")
		self.solon.rendertemplate("template/sitemap.txt")
		self.solon.rendertemplate("template/robots.txt", keepWhitespace=True)
		self.solon.rendertemplate("template/rss.tpl")

		# write the output content to their corresponding output files

		self.writeoutput()


class BaseException(Exception):
	def __init__(self, message):
		self.message = message

	def __str__(self):
		return self.message

class NoConversion(BaseException):
	def __init__(self, message):
		BaseException.__init__(self, message)


def processargs(argv):

	configname = 'config.yml'
	tgtdir = "_http"
	dbg_site_url = 'http://localhost:8000'
	tgtsubdir = None
	publish_all = False
	debug = False
	srcdir = None
	verbose = 0

	try:
		optlist, args = getopt.gnu_getopt(argv[1:], 's:dc:T:t:pvh', ['sourcedir=', 'debug', 'config=', 'targetdir=', 'targetsubdir=', 'publish-all', 'verbose', 'help'])
	except getopt.GetoptError as err:
		usage(-2, argv[0], err)
	for opt, arg in optlist:
		if opt in ('-c', '--config'):
			configname = arg
		elif opt in ('-s', '--sourcedir'):
			srcdir = arg
		elif opt in ('-T', '--targetdir'):
			tgtdir = arg
		elif opt in ('-t', '--targetsubdir'):
			tgtsubdir = arg
		elif opt in ('-p', '--publish-all'):
			publish_all = True
		elif opt in ('-h', '--help'):
			usage(0, argv[0], '')
		elif opt in ('-d', '--debug'):
			debug = True
		elif opt in ('-v', '--verbose'):
			verbose += 1
		else:
			usage(-1, argv[0], "unknown argument [%s]" % opt)
	if len(args) > 0:
		usage(-1, argv[0], "illegal arguments: %s" % (" ".join(args)))

	if srcdir is None:
		srcdir = os.path.split(configname)[0]

	config = nsdict.NSDict(yaml.safe_load(readfile(configname)))

	config['config'].update({
		'srcdir' 						: srcdir,
		'tgtdir' 						: tgtdir,
		'base_path'						: '',
		'publish_all'					: publish_all,
		'debug'							: debug,
		'verbose' 						: verbose,
	})

	if tgtsubdir:
		config['config/tgtsubdir'] = tgtsubdir

	if debug:
		config['config/site_url'] = dbg_site_url
	
	return config

def usage(exitcode, program, message):

	# add a --verbose option, think about logging different aspects of the situation
	# remove all mention of traceback and pdb, we can do this with python -m pdb
	# at some point, think about breaking up the actions (removing the source tree, copying the static files, making a render list, etc.)
	if message:
		print message
	print """\
Usage: %s [-d|--debug] [-c|--config=<CONF>] [-t|--targetsubdir=<DIR>] [-T|--targetdir=<DIR>] [-p|--publish-all] [-v|--verbose] [--help]
Where:
	--debug specifies the site should be built to debug
	--config=<CONFIG> specifies where to find the CONFIG file
	--targetdir=<DIR> specifies the output to go to the subdirectory DIR. This directory
		will be deleted & recreated during the running of the program!
		This defaults to "_http"
	--publish-all will publish all content, even if marked 'nopublish'
	--verbose increases the verbosity of the output
		If specified more than once, all library calls will be made verbose
	--help prints this help and exits
""" % program
	sys.exit(exitcode)


if __name__=="__main__":
	config = processargs(sys.argv)

	rezyn = Rezyn(config)
	rezyn.process()



