#!/usr/bin/env python3

import sys
import os
import os.path
import re

import yaml
import datetime
import dateutil.parser
import shutil
import hashlib

import nsdict

import xml.sax.saxutils
import lxml.html
import lxml.etree
import bbcode
import markdown

import template.site
import template.rss
import template.sitemap
import template.robots

import pdb


""" 
So the idea is to read in the entries in the blog, and output the pages
via airium.

We read in structured data, ie. our blog posts are read into a Blog class,
project posts into a Project class, etc.

We can then use functions such as 
	for blog in blogs:
		makeblog(blog)
which will output each blog post into a file using makeblog.
Let's do this top down, ie start at the main output method

"""

def log(*args, **kwargs):
	print(*args, **kwargs)
	pass

class Generator:

	def __init__(self, argv):

		self.configfile = "config.yml" # the default file

		# read the config.yml file
		with open(self.configfile) as f:
			self.config = nsdict.NSDict(yaml.safe_load(f))

		self.config["current_year"] = datetime.datetime.now().year
		print(str(self.config))

		self.bbparser = bbcode.Parser(replace_links=False, replace_cosmetic=False, newline="")
		self.bbparser.add_simple_formatter('img', '<img src="%(value)s" loading="lazy" />')
		self.bbparser.add_simple_formatter('gallery', '<div class="gallery slides">%(value)s</div>')
		self.bbparser.add_simple_formatter('youtube', '<iframe width="640" height="390" src="https://www.youtube.com/embed/%(value)s" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen="True">_</iframe>')

	def splitheader(self, text):
		header, body = "", text # default is no header
		parts = re.split("---\n", text)
		if len(parts) > 1:
			if len(parts[0]) == 0 and len(parts) == 3:
				header, body = parts[1:]
		return header, body

	def texttohtml(self, ext, text):
		# convert the body text into an html snippet, if it is not an html file
		html = text # default
		if ext == '.md':
			html = markdown.markdown(text)
		elif ext == ".bb":
			if 0:
				# split the text into chunks, where chunks are separated by \n\n
				chunks = [chunk for chunk in [chunk.strip() for chunk in re.split("(\n\n+)", text)] if len(chunk) > 0]
				# replace all newlines with spaces, otherwise the rest of this code will paste words together weirdly
				chunks = [chunk.replace("\n", " ") for chunk in chunks]
				parsed = [self.bbparser.format(chunk) for chunk in chunks]
				joins = [lxml.html.tostring(lxml.html.fromstring(chunk), encoding="unicode") for chunk in parsed]
				html = "\n".join(joins)
			# split the text into groups at double-newline delimiters
			texts = [line.strip() for line in re.split(r"\n\n+", text)]
			# format each chunk independently
			parsed = [self.bbparser.format(line) for line in texts if line != '']
			# join all the chunks together, wrapping non-element chunks into paragraphs
			html = "\n".join(["<p>" + chunk + "</p>" if chunk[0] != "<" else chunk for chunk in parsed])
		return html

	def imgurmodifier(self, src, modifier):
		"""
			s =   90×  90 = Small Square (as seen in the example above)
			b =  160× 160 = Big Square 
			t =  160× 160 = Small Thumbnail 
			m =  320× 320 = Medium Thumbnail 
			l =  640× 640 = Large Thumbnail
			h = 1024×1024 = Huge Thumbnail
		"""
		imgururl = "https://i.imgur.com"
		extra = "/TFJEC0j" # example extra junk on imgur urls
		if src[:len(imgururl)] == imgururl:
			# add the modifier
			base, ext = os.path.splitext(src)
			assert(len(base) == len(imgururl) + len(extra))
			if len(base) == len(imgururl) + len(extra):
				src = base + modifier + ext
		return src

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
		with open(filename, "r") as f:
			#filecontent = unicode(f.read(), encoding="utf-8")
			filecontent = f.read()
		# split the yaml frontmatter and body text
		fileheader, filebody = self.splitheader(filecontent)
		metadata = yaml.safe_load(fileheader)
		if metadata is not None:
			content.update(metadata)

		# escape any characters that need to be escaped in the title
		if 'title' in content:
			content['title'] = xml.sax.saxutils.escape(content['title'])

		# convert the date string in the metadata into a raw datetime we can work with
		if 'date' in content:
			content['date'] = dateutil.parser.parse(content['date'])

		# convert the body text into an html snippet, if it is not an html file
		text = self.texttohtml(ext.lower(), filebody)

		# create an xml representation of the document
		# we have to add a root element!
		root = lxml.html.fromstring(text)

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
				print(f"filename [{filename}] has an illegal (plain) imgur file: [{content.thumbnail}]")
				raise
		else:
			content['thumbnail'] = "https://i.imgur.com/sa6Wtvs.png"
		thumbnail = lxml.etree.Element("img")
		thumbnail.attrib["src"] = content['thumbnail']
		thumbnail.attrib["class"] = "thumbnail"
		thumbnail.attrib["loading"] = "lazy" # add lazy loading attribute
		content['thumbnail'] = lxml.html.tostring(thumbnail, encoding="unicode")

		# TODO: we want to replace images with linked images.
		# Ie. for an <img data-src="..."/>, we want an <a href="..."><img src="src" /></a>
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

			if 0:
				# reparent the image to a new hyperlink:
				parent = img.getparent()
				newlink = lxml.html.fromstring("<a />")
				newlink.attrib["href"] = datasrc #self.imgurmodifier(datasrc, "h") # make a Huge Thumbnail, if possible
				newlink.append(img)
				parent.append(newlink)

		text = lxml.html.tostring(root, encoding="unicode")
		# finally add the text
		content['content'] = text

		# and add a comments section:
		content['comments'] = []

		return content

	def readcontent(self, contentpath):
		self.content = nsdict.NSDict()
		#log(f"loading content from [{contentpath}]")
		for dirName, subdirList, fileList in os.walk(contentpath):
			root = dirName[len(contentpath)+1:]
			for fileName in fileList:
				if fileName == ".DS_Store":
					continue
				fullpath = os.path.join(dirName, fileName)
				filecontent = self.readfile(fullpath)
				if self.config.get("publish_all", False) or "nopublish" not in filecontent:
					base, ext = os.path.splitext(fileName)
					var = os.path.join(root, base)
					#log(f"readcontent: adding content [{var}]")
					self.content[var] = filecontent

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

	def readcomments(self, commentspath):
		# read comment files from the directory
		log("loading comments from [%s]" % commentspath)

		# load every comment into a lookup table
		comments = []
		commentlookup = {}
		for dirName, subdirList, fileList in os.walk(commentspath):
			root = dirName[len(commentspath)+1:]
			for fileName in fileList:
				if fileName == ".DS_Store":
					continue
				fullpath = os.path.join(dirName, fileName)
				var = os.path.join("content", root, fileName)
				log("adding comment ", var)
				comment = self.readfile(fullpath)
				commenturi = comment.pageuri + "#comment" + str(comment.commentid)
				commentlookup[commenturi] = comment
				comments.append(comment)

		# sort the comments by their date
		# this means that they will appear in order on the page, no matter when they were added
		comments = sorted(comments, key=lambda comment: comment.date)

		# use the lookup table to create the trees of comments, attaching the root
		# of each tree to its page
		for comment in comments:
			commenturi = comment.pageuri + "#comment" + str(comment.commentid)
			if comment.replytoid is not None:
				# this is a reply
				replytouri = comment.pageuri + "#comment" + str(comment.replytoid)
				try:
					# add this comment to that comment's reply list:
					parent = commentlookup[replytouri]
				except KeyError:
					log("orphan reply comment:", comment.commentid)
					continue
				parent['comments'].append(comment)
				# add the replyingto field (this is used by RSS)
				comment['replyingto'] = parent.displayname
			else:
				# this must be a root comment.
				# is there a comment with the same pageid/replyto?
				pageuri, ext = os.path.splitext(comment.pageuri)
				try:
					page = self.content[pageuri]
				except KeyError:
					log("orphan comment:", comment.commentid)
					continue
				page.comments.append(comment)

	def renamefileswithchecksums(self):
		filepaths = [
			"css/structure.css",
			"css/style.css",
			"css/widescreen.css",
			"css/smallscreen.css",
			"css/radiant.css",
			"js/radiant.js",
		]
		for filepath in filepaths:
			oldfilepath = os.path.join(self.config.outputdir, self.config.tgtsubdir, filepath)
			checksum = hashlib.md5(open(oldfilepath,'rb').read()).hexdigest()
			base, ext = os.path.splitext(filepath)
			newfilename = f"{base}-{checksum}{ext}"
			newfilepath = os.path.join(self.config.outputdir, self.config.tgtsubdir, newfilename)
			shutil.move(oldfilepath, newfilepath)
			self.content[os.path.join("filekeys", filepath)] = os.path.join("/", newfilename)

	def run(self):

		# read all markdown blog posts, project posts, etc.
		self.readcontent(self.config.contentdir)
		# read all the comment posts
		self.readcomments(self.config.commentsdir)

		# gather all the tags across all the blog posts, and reference the posts that use each tag
		tags = {}
		for post, values in self.content.blog.items():
			if 'tags' in values and values['tags'] is not None:
				for tag in values['tags']:
					tags.setdefault(tag, [])
					# what if we instead append the values here? As in, we don't have to look the post up again, we can just use
					# the values... Or heck, both.
					tags[tag].append(post)

		blogposts = self.content.blog.values()
		sketches = self.content.sketches.values()
		articles = self.content.articles.values()
		projects = self.content.projects.values()

		sortedblogposts = sorted(blogposts, key=lambda values: values['date'], reverse=True)
		self.content["sortedblogposts"] = sortedblogposts

		sortedprojects = sorted(projects, key=lambda values: values['date'], reverse=True)
		for project in sortedprojects:
			projecttag = "project:" + project['project']
			project['posts'] = []
			if projecttag in tags:
				posts = [self.content.blog[post] for post in tags[projecttag]]
				sortedposts = sorted(posts, key=lambda values: values['date'], reverse=False)
				project['posts'] = sortedposts
		self.content["sortedprojects"] = sortedprojects

		sortedsketches = sorted(sketches, key=lambda values: values['date'], reverse=True)
		self.content["sortedsketches"] = sortedsketches

		sortedarticles = sorted(articles, key=lambda values: values['date'], reverse=True)
		self.content["sortedarticles"] = sortedarticles

		# the shop tag is handled differently, since we may want to add blog announcements, articles, projects and / or drawings to the shop
		sortedwares = []
		if 'shop' in tags:
			wares = [self.content.blog[post] for post in tags['shop'] if post in self.content.blog]
			sortedwares = sorted(wares, key=lambda values: values['date'], reverse=True)
		self.content["sortedwares"] = sortedwares

		targetdir = os.path.join(self.config.outputdir, self.config.tgtsubdir)
		# remove the target directory
		log("removing targetdir [%s]" % targetdir)
		try:
			shutil.rmtree(targetdir)
		except Exception as e:
			print("Exception:", e)
			pass
		# copy the static files
		shutil.copytree(self.config.staticdir, targetdir)
		#if self.config.get("debug", False):
		#	# web minify (css and js)
		#	log("minify web in targtdir [%s]" % targetdir)
		#	self.minifydir(targetdir)

		# # rename each css/js file with its checksum key
		self.renamefileswithchecksums()

		template.site.create(self.config, self.content)
		template.rss.create(self.config, self.content)
		template.sitemap.create(self.config, self.content)
		template.robots.create(self.config, self.content)



if __name__=="__main__":
	generator = Generator(sys.argv)
	generator.run()


