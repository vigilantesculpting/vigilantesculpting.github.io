#!/usr/bin/env python3 

import os
import datetime
import re
import pathlib

import airium2 as airium

import pdb

## helpers

def truncate(text):
	"""Truncates a piece of html text at the required number of words
	"""
	words = 25
	textwords = re.sub('(?s)<.*?>', ' ', text).split()[:words]
	shorttext = ' '.join(textwords)
	try:
		if len(shorttext) == 0:
			return shorttext
		if shorttext[-1] == ".":
			return shorttext + ".."
		return shorttext + " ..."
	except Exception as e:
		print(f"exception: {e}, shorttext: '{shorttext}'")
		raise

def radiant(doc):
	with doc.div(id = "radiant-lightbox"):
		doc.div(id = "radiant-lightbox-close", _t="&#x274C;")
		with doc.div(id = "radiant-lightbox-container1"):
			with doc.div(id = "radiant-lightbox-container"):
				doc.div(id = "radiant-lightbox-prev", _t = "&#10094;")
				doc.span(id = "radiant-lightbox-slot")
				doc.div(id = "radiant-lightbox-next", _t = "&#10095;")
		doc.div(id = "radiant-lightbox-text")
	return doc

def redirect(config, content, post):
	doc = airium.Airium(source_minify = config.airium.source_minify)
	doc.SINGLE_TAGS = [
		'input', 'hr', 'br', 'img', 'area', 'link',
		'col', 'meta', 'base', 'param', 'wbr',
		'keygen', 'source', 'track', 'embed',
	]
	doc("<!DOCTYPE html>")
	with doc.html(lang = "en"):
		with doc.head():
			doc(f"<meta http-equiv='Refresh' content='0; URL='{post.slug}.html'>")
			doc("<meta charset='UTF-8'>")

## page function

def page(config, content, title, body, base_path = "", meta = None):
	doc = airium.Airium(source_minify = config.airium.source_minify)
	doc("<!DOCTYPE html>")
	with doc.html(lang = "en"):
		with doc.head():
			doc.title(_t = f"{config.title} - {title}")
			if "googletag" in config:
				# google analytics
				doc("<!-- Global site tag (gtag.js) - Google Analytics -->")
				doc("<!-- Note: I am only sending anonymized IP address pageviews to Google. No other information is collected! -->")
				doc.script(Async=True, src=config.googletag) # "https://www.googletagmanager.com/gtag/js?id=G-RX7VS9VBWV")
				with doc.script():
					doc("window.dataLayer = window.dataLayer || [];")
					doc("function gtag(){dataLayer.push(arguments);}")
					doc("gtag('js', new Date());")
					doc("gtag('config', 'G-RX7VS9VBWV', {'anonymize_ip': true});")
				doc("<!-- End Google Analytics -->")
			# device viewport
			doc.meta(name = "viewport", content = "width=device-width")
			# favicon
			doc.link(href = os.path.join("/", config.tgtsubdir, "favicon.ico"), rel="icon", type="image/x-icon")
			# CSS
			doc.link(rel="stylesheet", type="text/css", href=f"{content.filekeys.css['structure.css']}")
			doc.link(rel="stylesheet", type="text/css", href=f"{content.filekeys.css['style.css']}")
			doc.link(rel="stylesheet", type="text/css", href=f"{content.filekeys.css['widescreen.css']}", media="screen and (min-width: 601px)")
			doc.link(rel="stylesheet", type="text/css", href=f"{content.filekeys.css['smallscreen.css']}", media="screen and (max-width: 600px)")
			# RSS links
			doc.link(rel="alternate", type="application/rss+xml", href=os.path.join("/", config.tgtsubdir, "blog",	   "rss.xml"), title="Blog RSS Feed")
			doc.link(rel="alternate", type="application/rss+xml", href=os.path.join("/", config.tgtsubdir, "projects", "rss.xml"), title="Projects RSS Feed")
			doc.link(rel="alternate", type="application/rss+xml", href=os.path.join("/", config.tgtsubdir, "articles", "rss.xml"), title="Articles RSS Feed")
			doc.link(rel="alternate", type="application/rss+xml", href=os.path.join("/", config.tgtsubdir, "sketches", "rss.xml"), title="Sketches RSS Feed")
			# Radiant lightobox
			#doc.link(rel="stylesheet", type="text/css", href=os.path.join("/", config.tgtsubdir, "css", content.filekeys.css["radiant.css"]))
			#doc.script(href=f"{content.filekeys.js['radiant.js']}")
			# evaluate any extra head tags that the caller wants to embed here
			if meta is not None:
				meta(doc)
		with doc.body():
			with doc.main():
				with doc.nav():
					with doc.section(klass = "titlesection"):
						with doc.a(href = os.path.join("/", config.tgtsubdir)):
							doc.div(klass = "titleimage").img(id = "titleimage", src = os.path.join("/", config.tgtsubdir, "images", "title.png"))
						with doc.div(klass = "sitenavigation"):
							#with doc.span("home").a(os.path.join("/", config.tgtsubdir)):
							#	doc("Home")
							with doc.ul(klass = "links"):
								doc.li().a(href = os.path.join("/", config.tgtsubdir, ""), 								_t = "Home")
								doc.li().a(href = os.path.join("/", config.tgtsubdir, "blog"), 							_t = "Blog")
								#doc.li().a(href = os.path.join("/", config.tgtsubdir, "gallery"), 						_t = "Gallery")
								doc.li().a(href = os.path.join("/", config.tgtsubdir, "projects"), 						_t = "Projects")
								doc.li().a(href = os.path.join("/", config.tgtsubdir, "sketches"), 						_t = "Sketches")
								#doc.li().a(href = os.path.join("/", config.tgtsubdir, "wip"), 							_t = "WIP")
								doc.li().a(href = os.path.join("/", config.tgtsubdir, "articles"), 						_t = "Articles")
								doc.li().a(href = os.path.join("/", config.tgtsubdir, "contact.html"), 					_t = "Contact")
								doc.li().a(href = os.path.join("/", config.tgtsubdir, "about.html"), 					_t = "About")
								doc.li().a(klass = 'highlightnav', href = os.path.join("/", config.tgtsubdir, "shop"),	_t = "Shop")
				# embed the body of the document here
				body(doc)

			# spacer to force the footer down
			#doc.div(klass = "vertspacer")

			with doc.footer():
				doc.section().p(_t = f"Content &copy; {config.current_year} Vigilante Sculpting")
				with doc.ul(klass = "links"):
					doc.li().a(href="https://www.artstation.com/g0rb", 			_t = "ArtStation")
					doc.li().a(href="https://www.deviantart.com/gorb", 			_t = "DeviantArt")
					doc.li().a(href="https://www.reddit.com/user/gorb314", 		_t = "Reddit")
					doc.li().a(href="https://instagram.com/gorb314", 			_t = "Instagram")
					doc.li().a(href="https://www.puttyandpaint.com/g0rb",	 	_t = "Putty & Paint")
					doc.li().a(href="http://www.coolminiornot.com/artist/gorb", _t = "CMON")
				#with doc.p():
				#	doc.a(href="https://www.artstation.com/g0rb", 			_t = "ArtStation")
				#	doc.a(href="https://www.deviantart.com/gorb", 			_t = "DeviantArt")
				#	doc.a(href="https://www.reddit.com/user/gorb314", 		_t = "Reddit")
				#	doc.a(href="https://instagram.com/gorb314", 			_t = "Instagram")
				#	doc.a(href="https://www.puttyandpaint.com/g0rb",	 	_t = "Putty & Paint")
				#	doc.a(href="http://www.coolminiornot.com/artist/gorb", 	_t = "CMON")

			#radiant(doc)

	return doc

def originalpost(doc, post):
	sources = {
		"puttyandpaint_url": "Putty&Paint",
		"artstation_url": "Artstation",
		"blogger_orig_url": "vigilantesculpting.blogspot.com",
		"cmon_post_url": "coolminiornot.com",
		"papermodellers_post_url": "papermodelers.com",
	}
	with doc.section().ul():
		for source, name in sources.items():
			if source in post:
				with doc.il().a(href = post[source]):
					doc(f"{name} link")
	return doc

def postsummary(doc, postpath, post):
	postlink = os.path.join(postpath, post.slug + ".html")
	# section? div?
	with doc.h2().a(href = postlink):
		doc(post.title)
	with doc.p(klass = "meta"):
		doc(f"Published on {datetime.datetime.strftime(post.date, '%Y/%m/%d @%H:%M:%S')} by <b>{post.author}</b>")
	if "thumbnail" in post:
		with doc.a(klass = "more", href = postlink):
			with doc.div(klass = "thumbnail-container"):
				if "nsfw" in post.tags:
					with doc.p(klass = "nsfw-warning"):
						doc("NSFW / Mature Content")
				doc(post.thumbnail)
	with doc.p(klass = "summary"):
		doc(f"{truncate(post.content)}&nbsp;")
	with doc.p(klass = "more").a(klass = "more", href = postlink):
		doc("Read more")
	return doc

def makeslides(doc, postpath, posts):
	with doc.section(klass = "slides"):
		for post in posts:
			with doc.div(klass = "slide"):
				postsummary(doc, postpath, post)

# ---------------------------------------------------------------------
#  Create the main index.html
# ---------------------------------------------------------------------

def mainindex(config, content):
	def body(doc):
		with doc.section(klass = "mainsection"):
			with doc.p():
				doc("Welcome to Vigilante Sculpting. This is where I post my sculpting, scratchbuilding, drawing and paintig work.")

		def mainslidesection(path, postpath, title, rsstitle, posts, readmoretext):
			with doc.section(klass = "mainsection"):
				with doc.div(klass = "postnav"):
					with doc.a(href = path).h1():
						doc(title)
					with doc.a(href = os.path.join("/", config.tgtsubdir, postpath, "rss.xml")):
						doc.div(klass = "postnav-right").img(src = os.path.join("/", config.tgtsubdir, "images/rss.png"), width = "32px", height = "32px", alt = rsstitle)
				makeslides(doc, postpath, posts)
				with doc.p().a(href = path):
					doc(f"{readmoretext} &#x300B;")
		mainslidesection('blog',	 'blog',	 'Latest News',						'News RSS Feed',	 content.sortedblogposts[:3], 'Read latest news on the blog')
		mainslidesection('projects', 'projects', 'Latest Projects',					'Projects RSS Feed', content.sortedprojects[:3],  'See more finished projects')
		mainslidesection('sketches', 'sketches', 'Latest Sketches &amp; Drawings', 	'Sketches RSS Feed', content.sortedsketches[:3],  'See more sketches &amp; drawings')
		mainslidesection('articles', 'articles', 'Latest Articles',					'Articles RSS Feed', content.sortedarticles[:3],  'Read more articles')

		def maintextsection(path, title, subtitle):
			with doc.section(klass = "mainsection"):
				with doc.a(href = path).h2():
					doc(title)
				with doc.p().a(href = path):
					doc(subtitle)

		maintextsection('contact.html', 'Contact me', 'Contact me')
		maintextsection('about.html', 'About me', 'Read more about this site and myself here')

	return page(config, content, title = 'Home', body = body) # base_path = '', meta = ''


# ---------------------------------------------------------------------
#  Create about and contact pages
# ---------------------------------------------------------------------

def about(config, content):
	return page(config, content, title = 'About me', body = lambda doc: doc(content.about_content.content))

def contact(config, content):
	return page(config, content, title = 'Contact me', body = lambda doc: doc(content.contact_content.content))


def postnavigation(doc, postid, posts, name):
	if len(posts) == 0:
		return
	with doc.section(klass = "postnav"):
		with doc.div(klass = "postnav-left"):
			if postid > 0:
				firstpost = posts[0]
				with doc.a(href = "latestpost.html").div(klass = "nextpost"):
					doc("&#x300A;")
				nextpost = posts[postid - 1]
				with doc.a(href = f"{nextpost.slug}.html", rel = "next").div(klass = "nextpost"):
					doc("&#x2329;")
			else:
				doc("&nbsp;")
		with doc.div(klass = "postnav-right"):
			if postid < len(posts) - 1:
				prevpost = posts[postid + 1]
				with doc.a(href = f"{prevpost.slug}.html", rel = "prev").div(klass = "prevpost"):
					doc("&#x232a;")
				lastpost = posts[-1]
				with doc.a(href = f"{lastpost.slug}.html").div(klass = "prevpost"):
					doc("&#x300B;")
			else:
				doc("&nbsp;")

# ---------------------------------------------------------------------
#  Create blog post pages
# ---------------------------------------------------------------------

def blogpost(config, content, postid, post, posts):
	path = os.path.join("blog", f"{post.slug}.html")
	commentpath = os.path.join(config.site_url, config.tgtsubdir, 'blog', f"{post.slug}.xml")
	def meta(doc):
		#doc.link(rel="alternate", type="application/rss+xml", title=f"Comments on '{post.title} - {config.title}", href=commentpath)
		pass
	def body(doc):
		postnavigation(doc, postid, posts, 'post')
		with doc.article():
			doc.h1(_t=post.title)
			with doc.p(klass = "meta"):
				doc(f"Published on {datetime.datetime.strftime(post.date, '%d/%m/%Y @%H:%M:%S')} by <b>{post.author}</b>")
			with doc.section(klass = "mainsection"):
				doc(post.content)
			originalpost(doc, post)
			with doc.ul(klass = "posttags"):
				for tag in post.tags:
					doc.li(_t=tag)
			#doc.div(klass="vertspacer")
		postnavigation(doc, postid, posts, 'post')
		#??? commentsection(post, path)
	return page(config, content, title = post.title, meta = meta, body = body)

def paginatenavigation(doc, pageid, pagecount, basename):
	if pagecount == 0:
		return
	with doc.section(klass = "postnav"):
		# for going forwards in time
		with doc.div(klass = "postnav-left"):
			if pageid == 0:
				doc("&nbsp;") # nothing to do, we are at the front (latest) page
			else:
				firstpage = f"{basename}.html"
				with doc.a(href = firstpage).div(klass = "prevpage"):
					doc("&#x300A;")
				prevpageid = pageid - 1 if pageid > 1 else ''
				prevpage = f"{basename}{prevpageid}.html"
				with doc.a(href = prevpage, rel = "prev").div(klass = "prevpage"):
					doc("&#x2329;")
		# for going backwards in time
		with doc.div(klass = "postnav-right"):
			if pageid < pagecount - 1:
				nextpageid = pageid + 1
				nextpage = f"{basename}{nextpageid}.html"
				with doc.a(href = nextpage, rel = "nextpage").div(klass = "nextpage"):
					doc("&#x232a;")
				lastpage = f"{basename}{pagecount - 1}.html"
				with doc.a(href = lastpage, rel = "nextpage").div(klass = "nextpage"):
					doc("&#x300B;")
			else:
				doc("&nbsp;")

def makegroups(items, groupsize):
	return [items[i*groupsize : i*groupsize + groupsize] for i in range(1 + len(items)//groupsize)]

def indexpage(config, content, pageid, postgroup, pagecount, title, targetdir, postsdir, description):
	def body(doc):
		with doc.div(klass = "postnav"):
			with doc.div():
				doc.h1(_t = title)
				if pagecount > 1:
					doc.h3(_t = f"Page {pageid + 1}/{pagecount}")
			with doc.a(href = os.path.join("/", config.tgtsubdir, targetdir, "rss.xml")):
				doc.div(klass = "postnav-right").img(src = os.path.join("/", config.tgtsubdir, "images/rss.png"), width = "32px", height = "32px", alt = f"{title} RSS Feed")
		paginatenavigation(doc, pageid, pagecount, "index")
		with doc.article():
			doc.p(_t = description)
			makeslides(doc, postsdir, postgroup)
			#doc.div(klass = "vertspacer")
		paginatenavigation(doc, pageid, pagecount, "index")
	return page(config, content, title = title, body = body)


def projectpost(config, content, projectid, pagecount, project, postgroupid, postgroup):
	def meta(doc):
		# doc.link(rel="alternate", type="application/rss+xml", title=f"Comments on '{project.title} - {config.title}'", href=commentpath)
		pass
	def body(doc):
		with doc.article():
			postnavigation(doc, projectid, content.sortedprojects, "project")

			if postgroupid == 0:
				doc.h1(_t = project.title)
				doc.p(klass = "meta", _t = f"Published on {datetime.datetime.strftime(project.date, '%d/%m/%Y @%H:%M:%S')} by <b>{project.author}</b>")
				with doc.section(klass = "mainsection"):
					doc(project.content)
				with doc.ul(klass = "posttags"):
					for tag in project.tags:
						doc.li(_t = tag)

			if len(postgroup) > 0:
				with doc.section(klass = "stepxstep"):
					if len(postgroup) > 1:
						doc.h2(_t = f"Step by step (Steps {postgroupid*config.paginatecount + 1} thru {postgroupid*config.paginatecount + len(postgroup)} of {len(project.posts)})")
					doc.p(_t = "These are the posts I made during the making of this project, in chronological order")
					paginatenavigation(doc, postgroupid, pagecount, project.slug)
					makeslides(doc, "../blog", postgroup)
					paginatenavigation(doc, postgroupid, pagecount, project.slug)

			postnavigation(doc, projectid, content.sortedprojects, "project")
		# commentsection(project, path)
	return page(config, content, title = project.title, meta = meta, body = body)

# used for blog/index[].html, articles/index[].html, projects/index[].html and sketches/index[].html
def makeindex(config, content, title, targetdir, posts, postsdir, description):
	postgroups = makegroups(posts, config.paginatecount)
	pagecount = len(postgroups)
	for pageid, postgroup in enumerate(postgroups):
		pagenumber = pageid if pageid > 0 else ''
		filename = os.path.join(targetdir, f"index{pagenumber}.html")
		output(config, indexpage(config, content, pageid, postgroup, pagecount, title, targetdir, postsdir, description.content), filename)


# ---------------------------------------------------------------------
#  Create the blog/ projects/ sketches & articles index pages
# ---------------------------------------------------------------------

def output(config, doc, filename):
	filepath = os.path.join(config.outputdir, config.tgtsubdir, filename)
	dname, fname = os.path.split(filepath)
	pathlib.Path(dname).mkdir(parents=True, exist_ok=True)
	with open(filepath, 'w') as f:
		f.write(str(doc))

def create(config, content):
	print("creating site content")

	output(config, mainindex(config, content), "index.html")

	output(config, about(config, content), "about.html")
	output(config, contact(config, content), "contact.html")

	for postid, post in enumerate(content.sortedblogposts):
		filename = os.path.join("blog", f"{post.slug}.html")
		output(config, blogpost(config, content, postid, post, content.sortedblogposts), filename)

	for postid, post in enumerate(content.sortedsketches):
		filename = os.path.join("sketches", f"{post.slug}.html")
		output(config, blogpost(config, content, postid, post, content.sortedsketches), filename)

	for postid, post in enumerate(content.sortedarticles):
		filename = os.path.join("articles", f"{post.slug}.html")
		output(config, blogpost(config, content, postid, post, content.sortedarticles), filename)

	makeindex(config, content, "Blog", 					"blog", 	content.sortedblogposts, 	"", 	content.blog_content)
	makeindex(config, content, "Projects", 				"projects", content.sortedprojects, 	"", 	content.projects_content)
	makeindex(config, content, "Sketches & Drawings", 	"sketches", content.sortedsketches, 	"", 	content.sketches_content)
	makeindex(config, content, "Articles",				"articles", content.sortedarticles, 	"", 	content.articles_content)
	makeindex(config, content, "Shop", 					"shop", 	content.sortedwares, 		"", 	content.shop_content)

	# create the redirect pages, so we don't have to keep modiying older pages to get to the latest page

	#output(config, redirect(config, content, content.sortedblogposts[0]), 	"blog/latestposts.html")
	#output(config, redirect(config, content, content.sortedsketches[0]), 	"projects/latestposts.html")
	#output(config, redirect(config, content, content.sortedarticles[0]), 	"sketches/latestposts.html")
	#output(config, redirect(config, content, content.sortedwares[0]), 		"articles/latestposts.html")

	# ---------------------------------------------------------------------
	#  Create the individual project pages
	# ---------------------------------------------------------------------

	for projectid, project in enumerate(content.sortedprojects):
		postgroups = makegroups(project.posts, config.paginatecount)
		pagecount = len(postgroups)
		path = os.path.join("projects", f"{project.slug}.html")
		commentpath = os.path.join(config.site_url, config.tgtsubdir, "projects", f"{project.slug}.xml")
		for postgroupid, postgroup in enumerate(postgroups):
			pagenum = postgroupid if postgroupid > 0 else ""
			filename = os.path.join("projects", f"{project.slug}{pagenum}.html")
			output(config, projectpost(config, content, projectid, pagecount, project, postgroupid, postgroup), filename)
		
