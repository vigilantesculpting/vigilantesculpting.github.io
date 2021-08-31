#!/usr/bin/env python

import sys
import os

import re
import getopt
import bbcode
import yaml
import lxml.html
import lxml.etree
import datetime
import dateutil.parser

import rezyn
import nsdict

# Internal debugging / tracing
LOG = False
def log(*args, **kwargs):
	if LOG:
		for arg in args:
			sys.stderr.write(str(arg))
		sys.stderr.write("\n")

def setlog(level):
	if level > 0:
		global LOG
		LOG = True
		rezyn.setlog(level - 1)

class Processor(rezyn.Rezyn):

	def __init__(self, config):
		rezyn.Rezyn.__init__(self, config)

		self.bbparser = bbcode.Parser(replace_links=False, newline="")
		self.bbparser.add_simple_formatter('img', '<img src="%(value)s" loading="lazy" />')
		self.bbparser.add_simple_formatter('gallery', '<div class="gallery slides">%(value)s</div>')
		self.bbparser.add_simple_formatter('youtube', '<iframe width="640" height="390" src="https://www.youtube.com/embed/%(value)s" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen="True">_</iframe>')

	def imgurmodifier(self, src, modifier):
		imgururl = "https://i.imgur.com"
		extra = "/TFJEC0j" # example extra junk on imgur urls
		if src[:len(imgururl)] == imgururl:
			# add the modifier
			base, ext = os.path.splitext(src)
			assert(len(base) == len(imgururl) + len(extra))
			if len(base) == len(imgururl) + len(extra):
				src = base + modifier + ext
		return src

	def parsebb(self, text):
		# split the text into chunks, where chunks are separated by \n\n
		chunks = [chunk for chunk in [chunk.strip() for chunk in re.split("(\n\n+)", text)] if len(chunk) > 0]
		# replace all newlines with spaces, otherwise the rest of this code will paste words together weirdly
		chunks = [chunk.replace("\n", " ") for chunk in chunks]
		parsed = [self.bbparser.format(chunk) for chunk in chunks]
		joins = [lxml.html.tostring(lxml.html.fromstring(chunk)) for chunk in parsed]
		html = "\n".join(joins)
		return html

	def readfile(self, filename):
		"""Read content and metadata from file into a dictionary."""
		#log("readfile:", filename)

		# Read default metadata and save it in the content dictionary.
		path, ext = os.path.splitext(filename)
		dirpath, base = os.path.split(path)
		content = nsdict.NSDict({
			'slug': base,
			'tags': [],
		})

		# Read file content.
		filecontent = unicode(rezyn.readfile(filename), encoding='utf-8')

		# split the yaml frontmatter and body text
		fileheader, filebody = rezyn.splitheader(filecontent)
		metadata = yaml.safe_load(fileheader)
		if metadata is not None:
			content.update(metadata)

		# convert the date string in the metadata into a raw datetime we can work with
		if 'date' in content:
			content['date'] = dateutil.parser.parse(content['date'])

		# convert the body text into an html snippet, if it not an html file
		text = self.texttohtml(ext.lower(), filebody)

		# create an xml representation of the document
		# we have to add a root element!
		root = lxml.html.fromstring("<div class='filecontent'>" + text + "</div>")

		# find all images, and prepare them for lightbox
		imgs = root.findall(".//img")
		if 'thumbnail' not in content and len(imgs) > 0:
			# if thumbnail was not set, and we have images, set it to the first image
			content['thumbnail'] = imgs[0].attrib["src"]
		# if we have a thumbnail now, use it
		if 'thumbnail' in content:
			try:
				content['thumbnail'] = self.imgurmodifier(content['thumbnail'], "m") # <-- modify it if possible.
			except AssertionError as e:
				print "filename [%s] has an illegal (plain) imgur file: [%s]" % (filename, content['thumbnail'])
				raise
			thumbnail = lxml.etree.Element("img")
			thumbnail.attrib["src"] = content['thumbnail']
			thumbnail.attrib["class"] = "thumbnail"
			thumbnail.attrib["loading"] = "lazy" # add lazy loading attribute
			content['thumbnail'] = lxml.html.tostring(thumbnail)

		for img in imgs:
			# if the image has no data-src, then grab the src, modify it (if possible), and add the original to data-src:
			datasrc = img.attrib['data-src'] if 'data-src' in img.attrib else img.attrib['src']
			# if the image is part of a gallery, resize it to medium, otherwise large
			parent = img.getparent()
			if parent is not None and "class" in parent.attrib and "gallery" in parent.attrib["class"]:
				imgsrc = self.imgurmodifier(img.attrib['src'], "m") # make a Large Thumbnail, if possible
			else:
				imgsrc = self.imgurmodifier(img.attrib['src'], "l") # make a Large Thumbnail, if possible

			# For the radiant lightbox
			img.attrib["class"] = "radiant-lightbox-slide"
			img.attrib["data-src"] = datasrc
			img.attrib["src"] = imgsrc

		text = lxml.html.tostring(root)
		# finally add the text
		content['content'] = text

		return content

	def gettagsfromposts(self, posts):
		tags = {}
		for post, values in posts.iteritems():
			if 'tags' in values and values['tags'] is not None:
				for tag in values['tags']:
					tags.setdefault(tag, [])
					tags[tag].append(post)
		return tags

	def process(self):

		setlog(self.solon.context['config/verbose'])

		log(">>> setup")

		self.setup()

		#### Read in website content + templates

		log(">>> read")

		self.readcontent(self.solon.context["config/contentdir"])
		self.readtemplates(self.solon.context["config/templatedir"])

		# post process the data

		log(">>> process")

		tags = self.gettagsfromposts(self.solon.context["content/blog"])
		#log("found tags:", " ".join(tags.keys()))

		blogposts = [self.solon.context['content/blog'][post] for post in self.solon.context['content/blog'].keys()]
		sortedblogposts = sorted(blogposts, key=lambda values: values['date'], reverse=True)
		self.solon.context['content/sortedblogposts'] = sortedblogposts

		projects = [self.solon.context['content/projects'][project] for project in self.solon.context['content/projects'].keys()]
		sortedprojects = sorted(projects, key=lambda values: values['date'], reverse=True)
		for project in sortedprojects:
			projecttag = "project:" + project['project']
			if projecttag in tags:
				posts = [self.solon.context['content/blog'][post] for post in tags[projecttag]]
				sortedposts = sorted(posts, key=lambda values: values['date'], reverse=False)
				project['posts'] = sortedposts
			else:
				project['posts'] = []
		self.solon.context['content/sortedprojects'] = sortedprojects

		if 'sketch' in tags:
			sketches = [self.solon.context['content/blog'][post] for post in tags['sketch']]
			sortedsketches = sorted(sketches, key=lambda values: values['date'], reverse=True)
		else:
			sortedsketches = []
		self.solon.context['content/sortedsketches'] = sortedsketches

		if 'article' in tags:
			articles = [self.solon.context['content/blog'][post] for post in tags['article']]
			sortedarticles = sorted(articles, key=lambda values: values['date'], reverse=True)
		else:
			sortedarticles = []
		self.solon.context['content/sortedarticles'] = sortedarticles

		# render the templates

		log(">>> render")

		self.solon.rendertemplate("template/site.tpl")
		self.solon.rendertemplate("template/sitemap.txt")
		self.solon.rendertemplate("template/rss.tpl")
		self.solon.rendertemplate("template/robots.txt", keepWhitespace=True)

		log(">>> write")

		self.writeoutput()


def run(argv):
	config = rezyn.processargs(argv)

	processor = Processor(config)
	processor.process()


if __name__=="__main__":
	run(sys.argv)

