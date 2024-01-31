#!/usr/bin/env python3

import os
import re
import datetime
import pathlib

from aquarium import Rss

def truncate(text):
	"""Truncates a piece of html text at the required number of words
	"""
	words = 25
	textwords = re.sub('(?s)<.*?>', ' ', text).split()[:words]
	return ' '.join(textwords)

# ---------------------------------------------------------------------
#  Functions for the RSS feeds
# ---------------------------------------------------------------------

def rsspage(config, content, body):
	doc = Rss()
	with doc.rss(version="2.0", xmlns="http://backend.userland.com/rss2", 
			_xmlns__tags="https://vigilantesculpting.github.io/tagsModule/", 
			_xmlns__conversation="https://vigilantesculpting.github.io/conversationModule/"):
		with doc.channel():
			body(doc)
	return doc

def item(doc, config, content, path, post):
	postlink = os.path.join(config.site_url, config.tgtsubdir, path, f"{post.slug}.html")
	with doc.item():
		doc.title(_t=post.title)
		doc.link(_t=postlink)
		with doc.description():
			doc("<![CDATA[")
			if "nsfw" in post.tags:
				with doc.p().b():
					doc("! NSFW !")
			if "thumbnail" in post:
				with doc.a(klass="more", href=postlink):
					doc(post.thumbnail)
			doc(f"{truncate(post.content)}&nbsp;")
			with doc.a(href=postlink):
				doc("[...Read More]")
			doc("]]>")
		with doc._tags__taglist():
			for tag in post.tags:
				doc._tags__tag(_t=tag)
		with doc.pubDate():
			doc(f"{datetime.datetime.strftime(post.date, '%%a, %%d %%b %%Y %%H:%%M:%%S %%z')}")
	return doc

def feed(config, content, title, posts, rsspath, postpath, description):
	def body(doc):
		doc.title(_t=title)
		doc.link(_t=f"{os.path.join(config.site_url, config.tgtsubdir, rsspath)}")
		doc.description(_t=description)
		for post in posts:
			item(doc, config, content, postpath, post)
	return rsspage(config, content, body)

# ---------------------------------------------------------------------
#  Functions for the comments RSS feeds
# ---------------------------------------------------------------------

def commentfeeditem(doc, config, content, comment):
	with doc.item():
		doc.title(_t=comment.displayname)
		doc.link(_t=f"{comment.pageuri}#comment{comment.commentid}")
		doc._conversation_comment(_t=comment.commentid)
		if comment.replytoid is not None and comment.replytoid > 0:
			doc._conversation_replyto(_t=comment.replyingto)
		with doc.description():
			if comment.replytoid > 0:
				doc.i(_t=f"(In reply to {comment.replyingto})")
			doc(comment.content)
	for replyitem in comment.comments:
		commentfeeditem(doc, config, content, replyitem)
	return doc


def commentfeed(config, content, post):
	def body(doc):
		doc.title(_t=f"Comment feed for '{post.title} - {config.title}'")
		doc.link(_t=os.path.join('blog', f"{post.slug}.html"))
		doc.description(_t=post.description)
		for comment in post.comments:
			commentfeeditem(doc, config, content, comment)
	return rsspage(config, content, body)

# ---------------------------------------------------------------------
#  Helper for an RSS page
# ---------------------------------------------------------------------

def output(config, doc, filename):
	filepath = os.path.join(config.outputdir, config.tgtsubdir, filename)
	#print(f"writing to filename [{filepath}]")
	dname, fname = os.path.split(filepath)
	pathlib.Path(dname).mkdir(parents=True, exist_ok=True)
	with open(filepath, 'w') as f:
		f.write(str(doc))


def create(config, content):
	# ---------------------------------------------------------------------
	#  Definitions for the RSS feeds
	# ---------------------------------------------------------------------

	latesttitle = f"{config.title} - Latest"
	latestdescr = 'Latest news about projects, sculpting, painting, drawing and model making'
	latestfile  = os.path.join('latest', 'rss.xml')

	blogtitle = f"{config.title} - Blog"
	blogdescr = 'Latest blog posts about sculpting, painting, drawing and model making'
	blogfile  = os.path.join('blog', 'rss.xml')

	projectstitle = f"{config.title} - Projects"
	projectsdescr = 'Latest scratchbuilt projects'
	projectsfile  = os.path.join('projects', 'rss.xml')

	articlestitle = f"{config.title} - Articles"
	articlesdescr = 'Latest articles about scratchbuilding, painting, and the hobby in general'
	articlesfile  = os.path.join('articles', 'rss.xml')

	sketchestitle = f"{config.title} - Sketches &amp; Drawings"
	sketchesdescr = 'Latest sketches and drawings'
	sketchesfile  = os.path.join('sketches', 'rss.xml')

	shoptitle = f"{config.title} - Shop"
	shopdescr = 'Latest stuff in the shop'
	shopfile  = os.path.join('shop', 'rss.xml')

	# ---------------------------------------------------------------------
	#  Render the RSS feeds
	# ---------------------------------------------------------------------

	output(config, feed(config, content, latesttitle,   content.latestposts, 	'latest', 	 'latest',     latestdescr), latestfile)

	output(config, feed(config, content, blogtitle,     content.sortedblogposts, 'blog', 	 'blog',     blogdescr), blogfile)
	output(config, feed(config, content, projectstitle, content.sortedprojects,  'projects', 'projects', projectsdescr), projectsfile)
	output(config, feed(config, content, sketchestitle, content.sortedsketches,  'sketches', 'blog',     sketchesdescr), sketchesfile)
	output(config, feed(config, content, articlestitle, content.sortedarticles,  'articles', 'blog',     articlesdescr), articlesfile)
	output(config, feed(config, content, shoptitle,     content.sortedwares,     'shop',     'shop',     shopdescr), shopfile)

	# ---------------------------------------------------------------------
	#  Render the comments RSS feeds
	# ---------------------------------------------------------------------
	if 0:
		for post in content.sortedblogposts:
			commentfile = os.path.join("blog", f"{post.slug}.xml")
			output(config, commentfeed(config, content, post), commentfile)

		for project in content.sortedprojects:
			commentfile = os.path.join("project", f"{project.slug}.xml")
			output(config, commentfeed(config, content, project), commentfile)

