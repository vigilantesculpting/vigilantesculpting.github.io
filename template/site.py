#!/usr/bin/env python3 

import sys
import os
import datetime
import re
import pathlib
import unicodedata

from aquarium import Html
from multiprocessing.pool import ThreadPool


class Site:

	THREADS = 8

	def __init__(self, config, content):
		self.config = config
		self.content = content

	## helpers

	def truncate(self, text, words = 25):
		"""Truncates a piece of html text at the required number of words
		"""
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

	def redirect(self, post):
		doc = Html(source_minify = self.config.html_minify)
		with doc.html(lang = "en"):
			with doc.head():
				doc(f"<meta http-equiv='Refresh' content='3; URL=/{post.slug}.html'>")
				doc("<meta charset='UTF-8'>")
		return doc

	def comments(self, doc, post):
		""" requires a "comments" section in the frontmatter of the post:
			comments:
				host: mastodon.social
				username: ???
				id: ???
		Add a tool which sets the comments for a given post from the commandline,
		using defaults from the config if not provided.
		Something like ./addcomments.py <postfilename> <id> [-h <host>] [-u <username>]
		"""
		replylink = f"https://{post['comments-host']}/{post['comments-username']}/{post['comments-id']}"
		originalpost = f"https://{post['comments-host']}/api/v1/statuses/{post['comments-id']}/context"

		with doc.div(klass = "article-content"):
			doc.h2("Comments")
			with doc.p():
				doc("You can use your Mastodon account to view and reply to this ")
				doc.a("post", href = replylink)
				doc(".")
	# TODO: make the following a popup info box or something
	#		with doc.p():
	#			with doc.button(id="replyButton", href=replylink, onclick="showCommentsDialog()"):
	#				doc("Reply")
	#		with doc.dialog(id = "toot-reply", klass="mastodon", data_component="dialog"):
	#			doc.h3(f"Reply to {comments['username']}'s post")
	#			with doc.p():
	#				doc("""With an account on the Fediverse or Mastodon, you can respond to this post. 
	#Since Mastodon is decentralized, you can use your existing account hosted by another Mastodon 
	#server or compatible platform if you don't have an account on this one.""")
	#			with doc.p():
	#				doc("Copy and paste this URL into the search field of your favourite Fediverse app or the web interface of your Mastodon server.")
	#			with doc.div(klass = "copypaste"):
	#				doc.input(type="text", readonly="", value=replylink)
	#				with doc.button(klass="button", id="copyButton", onclick=f"copyCommentsDialog('{replylink}')"):
	#					doc("Copy")
	#				with doc.button(klass="button", id="cancelButton", onclick="closeCommentsDialog()"):
	#					doc("Close")
			with doc.p(id="mastodon-comments-list"):
				with doc.button(id="load-comment", onclick = f'loadComments("{originalpost}", {post["comments-id"]}, "{replylink}")'):
					doc("Load & display comments from Mastdon here")
			with doc.noscript().p():
				doc("You need JavaScript to view the comments!")

		doc.script(type="text/javascript", src=f"{self.content.filekeys.js['comments.js']}")

	## page function

	def page(self, title, body, base_path = "", meta = None):
		doc = Html(source_minify = self.config.html_minify)
		with doc.html(lang = "en"):
			with doc.head():
				doc.title(f"{self.config.title} - {title}")
				if "googletag" in self.config:
					# google analytics
					doc("<!-- Global site tag (gtag.js) - Google Analytics -->")
					doc("<!-- Note: I am only sending anonymized IP address pageviews to Google. No other information is collected! -->")
					doc.script(Async=True, src=self.config.googletag)
					with doc.script():
						doc("window.dataLayer = window.dataLayer || [];")
						doc("function gtag(){dataLayer.push(arguments);}")
						doc("gtag('js', new Date());")
						doc("gtag('config', 'G-RX7VS9VBWV', {'anonymize_ip': true});")
					doc("<!-- End Google Analytics -->")
				# device viewport
				doc.meta(name = "viewport", content = "width=device-width")
				# favicon
				doc.link(href = os.path.join("/", self.config.tgtsubdir, "favicon.ico"), rel="icon", type="image/x-icon")
				# CSS
				doc.link(rel="stylesheet", type="text/css", href="/css/page.css")
				# RSS links
				doc.link(rel="alternate", type="application/rss+xml", href=os.path.join("/", self.config.tgtsubdir, "blog",	   "rss.xml"), title="Blog RSS Feed")
				doc.link(rel="alternate", type="application/rss+xml", href=os.path.join("/", self.config.tgtsubdir, "projects", "rss.xml"), title="Projects RSS Feed")
				doc.link(rel="alternate", type="application/rss+xml", href=os.path.join("/", self.config.tgtsubdir, "articles", "rss.xml"), title="Articles RSS Feed")
				doc.link(rel="alternate", type="application/rss+xml", href=os.path.join("/", self.config.tgtsubdir, "sketches", "rss.xml"), title="Sketches RSS Feed")
				doc.link(rel="me", href="https://github.com/vigilantesculpting")
				#doc.link(rel="webmention", href="https://webmention.io/vigilantesculpting.com/webmention") # when we are ready...
				# Scripts
				doc.script(type="text/javascript", src=f"{self.content.filekeys.js['purify.js']}")
				doc.script(type="text/javascript", src=f"{self.content.filekeys.js['simple-lightbox.js']}")
				with doc.script():
					# Start the lightbox
					doc("""\
addEventListener('load', (event) => {
	let gallery = new SimpleLightbox('.gallery a');
});
""")
				# evaluate any extra head tags that the caller wants to embed here
				if meta is not None:
					meta(doc)
			with doc.body():
				with doc.nav():
					with doc.section(klass = "titlesection"):
						with doc.a(href = os.path.join("/", self.config.tgtsubdir)):
							doc.div(klass = "titleimage").img(id = "titleimage", src = os.path.join("/", self.config.tgtsubdir, "images", "header.png"), width = "900px") #"title.png"))
						with doc.div(klass = "sitenavigation"):
							#with doc.span("home").a(os.path.join("/", self.config.tgtsubdir)):
							#	doc("Home")
							with doc.ul(klass = "links"):
								doc.li().a("Home", 			href = os.path.join("/", self.config.tgtsubdir, "") 								)
								doc.li().a("Blog", 			href = os.path.join("/", self.config.tgtsubdir, "blog") 							)
								#doc.li().a("Gallery", 		href = os.path.join("/", self.config.tgtsubdir,"gallery") 							)
								doc.li().a("Projects", 		href = os.path.join("/", self.config.tgtsubdir, "projects")							)
								doc.li().a("Sketches", 		href = os.path.join("/", self.config.tgtsubdir, "sketches")							)
								#doc.li().a("WIP", 			href = os.path.join("/", self.config.tgtsubdir, "wip") 								)
								doc.li().a("Articles", 		href = os.path.join("/", self.config.tgtsubdir, "articles")							)
								doc.li().a("Contact", 		href = os.path.join("/", self.config.tgtsubdir, "contact.html") 					)
								doc.li().a("About", 		href = os.path.join("/", self.config.tgtsubdir, "about.html")						)
								doc.li().a("Shop", 			klass = 'highlightnav', href = os.path.join("/", self.config.tgtsubdir, "shop")		)
				with doc.main():
					# embed the body of the document here
					body(doc)

				# spacer to force the footer down
				#doc.div(klass = "vertspacer")

				with doc.footer():
					doc.section().p(f"Content &copy; {self.config.current_year} Vigilante Sculpting")
					with doc.ul(klass = "links"):
						doc.li().a("Mastodon",				href = "https://mastodon.social/@gorb314" 											)
						doc.li().a("Bluesky",				href = "https://bsky.app/profile/gorb314.bsky.social" 								)
						doc.li().a("ArtStation",			href = "https://www.artstation.com/g0rb" 											)
						doc.li().a("Reddit",				href = "https://www.reddit.com/user/gorb314" 										)
						doc.li().a("Putty & Paint",			href = "https://www.puttyandpaint.com/g0rb"	 										)
						doc.li().a("CMON",					href = "http://www.coolminiornot.com/artist/gorb"									)
						doc.li().a("GitHub",				href = "http://www.github.com/vigilantesculpting"									)
						doc.li().a("Thingiverse",			href = "https://www.thingiverse.com/gorb314/designs"								)
						doc.li().a("Etsy",					href = "https://www.etsy.com/shop/VigilanteSculpting"								)
						doc.li().a("Teepublic",				href = "https://www.teepublic.com/user/gorb"										)
					with doc.section().p():
						doc("Website hosted on ")
						with doc.a(href="http://www.github.com"):
							doc("Github")
					#with doc.section().p():
					#	doc("Images hosted on ")
					#	with doc.a(href="https://imgbb.com"):
					#		doc("ImgBB")
					with doc.a(href = os.path.join("/", self.config.tgtsubdir), klass = "titleimage"):
						doc.div(klass = "titleimage").img(id = "titleimage", src = os.path.join("/", self.config.tgtsubdir, "images", "footer.svg")) #"logo.png"))
					with doc.span(klass="h-card"):
						with doc.a(klass="u-url", rel="me", href="/"):
							doc("Chris (gorb314)")
						doc.img(klass="u-photo", src = os.path.join("/", self.config.tgtsubdir, "images", "jd-round.png"))
						doc.img(klass="u-featured", src = os.path.join("/", self.config.tgtsubdir, "images", "banner.jpg"))
				#radiant(doc)

		return doc

	def originalpost(self, doc, post):
		# TODO: modify the front matter so we have
		# 	originalpost:
		#   - url
		# we can then figure out from the url what site it was posted on, and we can have multiples without ruining the namespace
		sources = {
			"puttyandpaint_url": "Putty&Paint",
			"artstation_url": "Artstation",
			"blogger_orig_url": "vigilantesculpting.blogspot.com",
			"cmon_post_url": "coolminiornot.com",
			"papermodellers_post_url": "papermodelers.com",
		}
		foundsources = [(source, name) for (source, name) in sources.items() if source in post]
		if len(foundsources) > 0:
			with doc.p():
				doc("This post originally appeared on")
			with doc.ul():
				for source, name in foundsources:
					with doc.li():
						doc.a(name, href = post[source], rel="syndication", klass="u-syndication")
		return doc

	def syndication(self, doc, post):
		# TODO: modify the front matter so we have
		# 	syndications:
		#   - url
		# we can then figure out from the url what site it was posted on, and we can have multiples without ruining the namespace
		# Add a tool which adds / removes / edits a syndication url for a given post?
		# Something like 
		# ./syndication.py <postfilename>							lists all syndication
		# ./syndication.py <postfilename> <url>						adds syndication url
		# ./syndication.py <postfilename> -r <url>					removes syndication url
		# ./syndication.py <postfilename> -m <url> <newurl>			changes syndication url to new url
		syndications = {
		}
		foundplaces = [(site, name) for (site, name) in syndications.items() if site in post]
		if len(foundplaces) > 0:
			with doc.p():
				doc("This post can also be found on")
			with doc.ul():
				for place, name in foundplaces:
					with doc.li():
						doc.a(name, href = post[place], rel="syndication", klass="u-syndication")
		return doc

	TIMESTAMPFORMAT = '%Y/%m/%d' #@%H:%M:%S'

	def postmeta(self, doc, post):
		def getposttype(post):
			# check the slug
			return os.path.split(post.slug)[0]
		posttype = getposttype(post)
		posttypenames = {
			"blog": "Blog Post",
			"projects": "Project",
			"articles": "Article",
			"sketches": "Sketch",
		}
		doc("Published on ")
		with doc.span(klass = 'posttimestamp'):
			doc(f"{datetime.datetime.strftime(post.date, self.TIMESTAMPFORMAT)}") #" @%H:%M:%S')}")
		doc(" by ")
		with doc.span(klass = 'postauthor'):
			doc(f"{post.author}")
		with doc.ul(klass = "posttags"):
			with doc.li(klass = 'postflair'):
				doc.a(posttypenames[posttype], href = os.path.join("/", posttype))
			#with doc.li(klass = "taglink").a(href = os.path.join("/", posttype)):
			#	doc(posttypenames[posttype])
			for tag in post.tags:
				with doc.li(klass = "taglink"):
					doc.a(tag, href = os.path.join("/", "tags", f"{self.slugify(tag)}.html"))

	def postsummary(self, doc, postpath, post):
		# we need a canonical way to create the postpath from the post itself, instead of having to be passed a postpath parameter
		# Is this possible?
		postlink = os.path.join("/", self.config.tgtsubdir, f"{post.slug}.html")
		# section? div?
		with doc.h2(klass = "slide-title"):
			doc.a(post.title, href = postlink)
		with doc.div(klass = "slide-meta meta"):
			self.postmeta(doc, post)
		if "thumbnail" in post:
			with doc.a(klass = "slide-thumbnail more", href = postlink):
				with doc.div(klass = "thumbnail-container"):
					if "nsfw" in post.tags:
						with doc.p(klass = "nsfw-warning"):
							doc("NSFW / Mature Content")
					doc(post.thumbnail)
		with doc.p(klass = "slide-summary summary"):
			doc(f"{self.truncate(post.content)}&nbsp;")
		return doc

	def makeslides(self, doc, postpath, posts):
		with doc.section(klass = "slides"):
			for post in posts:
				with doc.div(klass = "slide"):
					self.postsummary(doc, postpath, post)

	# ---------------------------------------------------------------------
	#  Create the main index.html
	# ---------------------------------------------------------------------

	def mainindex(self):
		def body(doc):
			with doc.section(klass = "mainsection"):
				with doc.p():
					doc("Welcome to Vigilante Sculpting. This is where I post my sculpting, scratchbuilding, drawing and paintig work.")

			# TODO: for each slide we need a marker (BLOGPOST, PROJECT, ARTICLE, SKETCH) to distinguish these things
			def mainslidesection(path, postpath, title, rsstitle, posts):
				with doc.section(klass = "mainsection"):
					with doc.div(klass = "postnav"):
						with doc.h1(): #a(href = path).h1():
							doc(title)
						with doc.a(href = os.path.join("/", self.config.tgtsubdir, postpath, "rss.xml")):
							doc.div(klass = "postnav-right").img(src = os.path.join("/", self.config.tgtsubdir, "images/rss.png"), width = "32px", height = "32px", alt = rsstitle)
					self.makeslides(doc, postpath, posts)
			mainslidesection('latest', 'latest', 'Latest News', 'News RSS Feed',self.content.latestposts[:6])

			with doc.p():
				doc("For more content, continue on to ")
				with doc.a(href="projects"):
					doc("Projects")
				doc(", ")
				with doc.a(href="blog"):
					doc("Blog posts")
				doc(", ")
				with doc.a(href="sketches"):
					doc("Sketches")
				doc(" and ")
				with doc.a(href="articles"):
					doc("Articles")

			def maintextsection(path, title, subtitle):
				with doc.section(klass = "mainsection"):
					with doc.a(href = path).h2():
						doc(title)
					doc.p().a(subtitle, href = path)

		return self.page(title = 'Home', body = body)


	# ---------------------------------------------------------------------
	#  Create about and contact pages
	# ---------------------------------------------------------------------

	def about(self):
		return self.page(title = 'About me', body = lambda doc: doc(self.content.pages.about.content))

	def contact(self):
		return self.page(title = 'Contact me', body = lambda doc: doc(self.content.pages.contact.content))

	def postnavigation(self, doc, postid, posts, name):
		if len(posts) == 0:
			return
		with doc.section(klass = "postnav"):
			with doc.div(klass = "postnav-left"):
				if postid > 0:
					firstpost = posts[0]
					with doc.a(href = "latestpost.html").div(klass = "nextpost"):
						doc("&#x300A;")
					nextpost = posts[postid - 1]
					with doc.a(href = f"/{nextpost.slug}.html", rel = "next").div(klass = "nextpost"):
						doc("&#x2329;")
				else:
					doc("&nbsp;")
			with doc.div(klass = "postnav-right"):
				if postid < len(posts) - 1:
					prevpost = posts[postid + 1]
					with doc.a(href = f"/{prevpost.slug}.html", rel = "prev").div(klass = "prevpost"):
						doc("&#x232a;")
					lastpost = posts[-1]
					with doc.a(href = f"/{lastpost.slug}.html").div(klass = "prevpost"):
						doc("&#x300B;")
				else:
					doc("&nbsp;")

	# ---------------------------------------------------------------------
	#  Create blog post pages
	# ---------------------------------------------------------------------

	def slugify(self, value, allow_unicode=False):
		"""
		Taken from https://github.com/django/django/blob/master/django/utils/text.py
		Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
		dashes to single dashes. Remove characters that aren't alphanumerics,
		underscores, or hyphens. Convert to lowercase. Also strip leading and
		trailing whitespace, dashes, and underscores.
		"""
		value1 = str(value)
		if allow_unicode:
			value2 = unicodedata.normalize('NFKC', value1)
		else:
			value2 = unicodedata.normalize('NFKD', value1).encode('ascii', 'ignore').decode('ascii')
		value3 = re.sub(r'[^\w\s-]', '', value2.lower())
		value4 = re.sub(r'[-\s]+', '-', value3)#.strip('-_')
		#pdb.set_trace()
		return value4

	def formattags(self, doc, tags):
		with doc.ul(klass = "posttags"):
			for tag in tags:
				with doc.li(klass = "taglink").a(href = os.path.join("/", "tags", f"{self.slugify(tag)}.html")):
					doc(tag)

	def posttags(self, doc, tags):
		if len(tags) == 0:
			return
		"""
		tags are in a tags frontmatter:
				tags:
				- project:sentinel
				- wh40k
				- papercraft
				- resin
		Add a tool to (a) list (b) add (c) rename or (d) remove tags from a given post:
		./tags.py <postfile> 							lists tags for given postfile
		./tags.py <postfile> <tags...>					adds tags for given postfile
		./tags.py <postfile> -c							removes all tags from given postfile
		./tags.py <postfile> -r <tags...>				removes given tags from given postfile
		./tags.py <postfile> -m <tags...> newtag		replaces given tag(s) with a newtag in a given postfile
		"""
		with doc.section():
			doc.p("This post has been tagged with")
			with doc.ul(klass = "posttags"):
				self.formattags(doc, tags)

	def blogpost(self, postid, post, posts):
		"""
		Create a new blog post using a tool:
		./newblogpost "title" 							create a new blog post
		./newblogpost -n <type> "title" 				create a new type post, where type can be 'blog', 'sketch', 'article'
		./newblogpost -p <project> "title" 				create a new project post
		./newblogpost "title" -t <tags...>				create a new post, with the given tags
		This creates the file in the proper location, with a timestamped name, populates the front matter with the available info, and launches
		the $EDITOR with the given filename
		"""
		path = os.path.join(f"{post.slug}.html")
		commentpath = os.path.join(self.config.site_url, self.config.tgtsubdir, f"{post.slug}.xml")
		def meta(doc):
			#doc.link(rel="alternate", type="application/rss+xml", title=f"Comments on '{post.title} - {self.config.title}", href=commentpath)
			pass
		def body(doc):
			self.postnavigation(doc, postid, posts, 'post')
			with doc.article():
				doc.h1(post.title)
				with doc.p(klass = "meta"):
					self.postmeta(doc, post)
					#doc(f"Published on {datetime.datetime.strftime(post.date, self.TIMESTAMPFORMAT)} by <b>{post.author}</b>")
				with doc.section(klass = "mainsection"):
					doc(post.content)
				self.originalpost(doc, post)
				#self.posttags(doc, post.tags)
				#doc.div(klass="vertspacer")
			self.postnavigation(doc, postid, posts, 'post')
			if "comments-id" in post:
				self.comments(doc, post)
		return self.page(title = post.title, meta = meta, body = body)

	def paginatenavigation(self, doc, pageid, pagecount, basename):
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

	def makegroups(self, items, groupsize):
		if len(items) > 0:
			return [items[i*groupsize : i*groupsize + groupsize] for i in range(1 + len(items)//groupsize)]
		return []

	def indexpage(self, pageid, postgroup, pagecount, title, targetdir, postsdir, description):
		def body(doc):
			with doc.div(klass = "postnav"):
				with doc.div():
					doc.h1(title)
					if pagecount > 1:
						doc.h3(f"Page {pageid + 1}/{pagecount}")
				with doc.a(href = os.path.join("/", self.config.tgtsubdir, targetdir, "rss.xml")):
					doc.div(klass = "postnav-right").img(src = os.path.join("/", self.config.tgtsubdir, "images/rss.png"), width = "32px", height = "32px", alt = f"{title} RSS Feed")
			self.paginatenavigation(doc, pageid, pagecount, "index")
			with doc.article():
				doc.p(description)
				self.makeslides(doc, postsdir, postgroup)
				#doc.div(klass = "vertspacer")
			self.paginatenavigation(doc, pageid, pagecount, "index")
		return self.page(title = title, body = body)


	def projectpost(self, projectid, pagecount, project, stepxstepfilename):
		def meta(doc):
			# doc.link(rel="alternate", type="application/rss+xml", title=f"Comments on '{project.title} - {self.config.title}'", href=commentpath)
			pass
		def body(doc):
			with doc.article():
				self.postnavigation(doc, projectid, self.content.sortedprojects, "project")

				doc.h1(f"{project.title}")
				with doc.div(klass = 'meta'):
					self.postmeta(doc, project)
					#doc.p(klass = "meta", f"Published on {datetime.datetime.strftime(project.date, self.TIMESTAMPFORMAT)} by <b>{project.author}</b>")
				if stepxstepfilename is not None:
					with doc.a(href = os.path.join("/", self.config.tgtsubdir, stepxstepfilename)):
						doc.p("Step by step (blog posts related to this project)", klass = "meta")

				with doc.section(klass = "mainsection"):
					doc(project.content)

					#self.posttags(doc, project.tags)

				self.postnavigation(doc, projectid, self.content.sortedprojects, "project")
			if "comments-id" in project:
				self.comments(doc, project)
		return self.page(title = project.title, meta = meta, body = body)

	def projectpoststepxstep(self, projectid, pagecount, project, postgroupid, postgroup):
		def meta(doc):
			# doc.link(rel="alternate", type="application/rss+xml", title=f"Comments on '{project.title} - {self.config.title}'", href=commentpath)
			pass
		def body(doc):
			with doc.article():
				self.paginatenavigation(doc, postgroupid, pagecount, os.path.split(project.slug)[1])

				doc.h1(f"{project.title} : Step by Step ")
				doc.h2(f"{postgroupid*self.config.paginatecount + 1} thru {postgroupid*self.config.paginatecount + len(postgroup)} of {len(project.posts)})")
				with doc.div(klass = 'meta'):
					self.postmeta(doc, project)
					#doc.p(klass = "meta", f"Published on {datetime.datetime.strftime(project.date, self.TIMESTAMPFORMAT)} by <b>{project.author}</b>")
				with doc.p():
					doc("These are the posts I made during the making of ")
					with doc.a(href = os.path.join("/", f"{project.slug}.html")):
						doc(f"{project.title}")
					doc(" in chronological order")

				with doc.section(klass = "stepxstep"):
					self.makeslides(doc, "../blog", postgroup)
				self.paginatenavigation(doc, postgroupid, pagecount, os.path.split(project.slug)[1])
		return self.page(title = project.title, meta = meta, body = body)


	# used for blog/index[].html, articles/index[].html, projects/index[].html and sketches/index[].html
	def makeindex(self, title, targetdir, posts, postsdir, description):
		postgroups = self.makegroups(posts, self.config.paginatecount)
		pagecount = len(postgroups)
		for pageid, postgroup in enumerate(postgroups):
			pagenumber = pageid if pageid > 0 else ''
			filename = os.path.join(targetdir, f"index{pagenumber}.html")
			self.output(self.indexpage(pageid, postgroup, pagecount, title, targetdir, postsdir, description.content), filename)

	def tagpage(self, pageid, postgroup, pagecount, tag):
		def meta(doc):
			#doc.link(rel="alternate", type="application/rss+xml", title=f"Tag: '{tag}'", href=commentpath)
			pass		
		def body(doc):
			with doc.article():
				self.paginatenavigation(doc, pageid, pagecount, f"{tag.name}")

				doc.h1(f"Posts tagged with '{tag.name}'")

				if pagecount > 1:
					doc.h3(f"Page {pageid + 1} of {pagecount}, with {len(tag.posts)} posts")
				else:
					doc.h3(f"{len(tag.posts)} posts")

				with doc.table(klass = "tagtable"):
					for post in postgroup:
						postlink = os.path.join("/", self.config.tgtsubdir, f"{post.slug}.html")
						with doc.tr():
							with doc.td(rowspan = 2, klass = "tagicon"):
								if "icon" in post:
									with doc.a(href = postlink):
										doc.img(src = post.icon, loading = "lazy", klass="iconthumbnail")
							with doc.td(klass = "tagtitle"):
								doc.a(post.title, href = postlink)
							with doc.td(klass = "tagdate"):
								doc(post.date)
						with doc.tr():
							with doc.td(colspan = 2):
								doc(self.truncate(post.content))

				self.paginatenavigation(doc, pageid, pagecount, f"{tag.name}")
		return self.page(title = f"Posts tagged with '{tag.name}'", meta = meta, body = body)

	def maketagpages(self, tagitem):
		tagslug, tag = tagitem
		postgroups = self.makegroups(tag.posts, self.config.paginatecount)
		pagecount = len(postgroups)
		for pageid, postgroup in enumerate(postgroups):
			pagenumber = pageid if pageid > 0 else ''
			filename = os.path.join(self.config.tgtsubdir, f"{tag.slug}{pagenumber}.html")
			self.output(self.tagpage(pageid, postgroup, pagecount, tag), filename)

	def maketagspages(self):
		with ThreadPool(processes = self.THREADS) as p:
			p.map(self.maketagpages, self.content.sortedtags.items())
		#for tagslug, tag in self.content.sortedtags.items():
		#	self.maketagpages(tag)

	def makeblogpost(self, blogpost):
		postid, post = blogpost
		filename = os.path.join(self.config.tgtsubdir, f"{post.slug}.html")
		self.output(self.blogpost(postid, post, self.content.sortedblogposts), filename)

	def makeblogposts(self):
		print("creating blog posts")
		#for blogpost in enumerate(self.content.sortedblogposts):
		#	self.makeblogpost(blogpost)
		with ThreadPool(processes = self.THREADS) as p:
			p.map(self.makeblogpost, enumerate(self.content.sortedblogposts))

		#for postid, post in enumerate(self.content.sortedblogposts):
		#	filename = os.path.join(self.config.tgtsubdir, f"{post.slug}.html")
		#	self.output(self.blogpost(postid, post, self.content.sortedblogposts), filename)

	# ---------------------------------------------------------------------
	#  Create the blog/ projects/ sketches & articles index pages
	# ---------------------------------------------------------------------

	def output(self, doc, filename):
		filepath = os.path.join(self.config.outputdir, self.config.tgtsubdir, filename)
		dname, fname = os.path.split(filepath)
		pathlib.Path(dname).mkdir(parents=True, exist_ok=True)
		with open(filepath, 'w') as f:
			f.write(str(doc))


	def create(self):
		print("creating site content")

		# make page css
		# we do this, because of the changing git-commit-stamped filenames for css that we produce.
		# This means that only the css files are updated, and each page does not have to be touched.
		with open(os.path.join(self.config.outputdir, self.config.tgtsubdir, "css", "page.css"), "w") as f:
			f.write(f"""
@import url('{self.content.filekeys.css['structure.css']}');
@import url('{self.content.filekeys.css['style.css']}');
@import url('{self.content.filekeys.css['smallscreen.css']}') only screen and (max-width: 600px);
@import url('{self.content.filekeys.css['widescreen.css']}') only screen and (min-width: 601px);
@import url('{self.content.filekeys.css["comments.css"]}');
@import url('{self.content.filekeys.css['simple-lightbox.css']}');
""")

		self.output(self.mainindex(), "index.html")
		self.output(self.about(), "about.html")
		self.output(self.contact(), "contact.html")

		print("creating blog posts")
		self.makeblogposts()

		print("creating sketch posts")
		def outputsketchpost(blogpost):
			postid, post = blogpost
			filename = os.path.join(self.config.tgtsubdir, f"{post.slug}.html")
			self.output(self.blogpost(postid, post, self.content.sortedsketches), filename)
		with ThreadPool(processes = self.THREADS) as p:
			p.map(outputsketchpost, enumerate(self.content.sortedsketches))
		#for postid, post in enumerate(self.content.sortedsketches):
		#	filename = os.path.join(self.config.tgtsubdir, f"{post.slug}.html")
		#	self.output(self.blogpost(postid, post, self.content.sortedsketches), filename)

		print("creating article posts")
		def outputarticlepost(blogpost):
			postid, post = blogpost
			filename = os.path.join(self.config.tgtsubdir, f"{post.slug}.html")
			self.output(self.blogpost(postid, post, self.content.sortedarticles), filename)
		with ThreadPool(processes = self.THREADS) as p:
			p.map(outputarticlepost, enumerate(self.content.sortedarticles))
		#for postid, post in enumerate(self.content.sortedarticles):
		#	filename = os.path.join(self.config.tgtsubdir, f"{post.slug}.html")
		#	self.output(self.blogpost(postid, post, self.content.sortedarticles), filename)

		print("creating sub indices")
		self.makeindex("Blog", 					"blog", 	self.content.sortedblogposts, 	"", 	self.content.pages.blog)
		self.makeindex("Projects", 				"projects", self.content.sortedprojects, 	"", 	self.content.pages.projects)
		self.makeindex("Sketches & Drawings", 	"sketches", self.content.sortedsketches, 	"", 	self.content.pages.sketches)
		self.makeindex("Articles",				"articles", self.content.sortedarticles, 	"", 	self.content.pages.articles)
		self.makeindex("Shop", 					"shop", 	self.content.sortedwares, 		"", 	self.content.pages.shop)

		# create the redirect pages, so we don't have to keep modiying older pages to get to the latest page

		self.output(self.redirect(self.content.sortedblogposts[0]), "blog/latestpost.html")
		self.output(self.redirect(self.content.sortedsketches[0]), 	"sketches/latestpost.html")
		self.output(self.redirect(self.content.sortedprojects[0]), 	"projects/latestpost.html")
		self.output(self.redirect(self.content.sortedarticles[0]), 	"articles/latestpost.html")
		self.output(self.redirect(self.content.sortedwares[0]), 	"shop/latestpost.html")

		# create the tags pages
		print("creating tag pages")
		self.maketagspages()

		# ---------------------------------------------------------------------
		#  Create the individual project pages
		# ---------------------------------------------------------------------

		print("creating project pages")
		for projectid, project in enumerate(self.content.sortedprojects):
			postgroups = self.makegroups(project.posts, self.config.paginatecount)
			pagecount = len(postgroups)
			path = os.path.join("projects", f"{project.slug}.html")
			commentpath = os.path.join(self.config.site_url, self.config.tgtsubdir, "projects", f"{project.slug}.xml")
			projectfilename = os.path.join(f"{project.slug}.html")
			firstpostfilename = os.path.join(f"{project.slug}0.html") if len(postgroups) > 0 else None
			self.output(self.projectpost(projectid, pagecount, project, firstpostfilename), projectfilename)
			for postgroupid, postgroup in enumerate(postgroups):
				filename = os.path.join(f"{project.slug}{postgroupid}.html")
				self.output(self.projectpoststepxstep(projectid, pagecount, project, postgroupid, postgroup), filename)


