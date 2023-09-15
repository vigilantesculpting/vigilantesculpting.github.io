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

	def comments(self, doc, comments):
		return # disable all comments for now

		""" requires a 
			comments:
				host: mastodon.social
				username: ???
				id: ???
		section in the front matter of a post
		Add a tool which sets the comments for a given post from the commandline,
		using defaults from the config if not provided.
		Something like ./addcomments.py <postfilename> <id> [-h <host>] [-u <username>]
		"""
		replylink = f"https://{comments['host']}/@{comments['username']}/{comments['id']}"
		originalpost = f"https://{comments['host']}/api/v1/statuses/{comments['id']}/context"

		with doc.div(klass = "article-content"):
			doc.h2(_t = "Comments")
			with doc.p():
				doc("You can use your Mastodon account to view and reply to this ")
				with doc.a(href = replylink):
					doc("post")
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
				with doc.button(id="load-comment", onclick = f"loadComments('{originalpost}', {comments['id']})"):
					doc("Load & display comments from Mastdon here")
			with doc.noscript().p():
				doc("You need JavaScript to view the comments!")

		doc.script(type="text/javascript", src=f"{self.content.filekeys.js['comments.js']}")

	## page function

	def page(self, title, body, base_path = "", meta = None):
		doc = Html(source_minify = self.config.html_minify)
		with doc.html(lang = "en"):
			with doc.head():
				doc.title(_t = f"{self.config.title} - {title}")
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
				doc.link(rel="stylesheet", type="text/css", href=f"{self.content.filekeys.css['structure.css']}")
				doc.link(rel="stylesheet", type="text/css", href=f"{self.content.filekeys.css['style.css']}")
				doc.link(rel="stylesheet", type="text/css", href=f"{self.content.filekeys.css['widescreen.css']}", media="screen and (min-width: 601px)")
				doc.link(rel="stylesheet", type="text/css", href=f"{self.content.filekeys.css['smallscreen.css']}", media="screen and (max-width: 600px)")
				# RSS links
				doc.link(rel="alternate", type="application/rss+xml", href=os.path.join("/", self.config.tgtsubdir, "blog",	   "rss.xml"), title="Blog RSS Feed")
				doc.link(rel="alternate", type="application/rss+xml", href=os.path.join("/", self.config.tgtsubdir, "projects", "rss.xml"), title="Projects RSS Feed")
				doc.link(rel="alternate", type="application/rss+xml", href=os.path.join("/", self.config.tgtsubdir, "articles", "rss.xml"), title="Articles RSS Feed")
				doc.link(rel="alternate", type="application/rss+xml", href=os.path.join("/", self.config.tgtsubdir, "sketches", "rss.xml"), title="Sketches RSS Feed")
				# Comments
				doc.script(type="text/javascript", src=f"{self.content.filekeys.js['purify.js']}")
				doc.link(rel="stylesheet", type="text/css", href=os.path.join("/", self.config.tgtsubdir, "css", self.content.filekeys.css["comments.css"]))
				# evaluate any extra head tags that the caller wants to embed here
				if meta is not None:
					meta(doc)
			with doc.body():
				with doc.nav():
					with doc.section(klass = "titlesection"):
						with doc.a(href = os.path.join("/", self.config.tgtsubdir)):
							doc.div(klass = "titleimage").img(id = "titleimage", src = os.path.join("/", self.config.tgtsubdir, "images", "title.png"))
						with doc.div(klass = "sitenavigation"):
							#with doc.span("home").a(os.path.join("/", self.config.tgtsubdir)):
							#	doc("Home")
							with doc.ul(klass = "links"):
								doc.li().a(href = os.path.join("/", self.config.tgtsubdir, ""), 								_t = "Home")
								doc.li().a(href = os.path.join("/", self.config.tgtsubdir, "blog"), 							_t = "Blog")
								#doc.li().a(href = os.path.join("/", self.config.tgtsubdir, "gallery"), 						_t = "Gallery")
								doc.li().a(href = os.path.join("/", self.config.tgtsubdir, "projects"), 						_t = "Projects")
								doc.li().a(href = os.path.join("/", self.config.tgtsubdir, "sketches"), 						_t = "Sketches")
								#doc.li().a(href = os.path.join("/", self.config.tgtsubdir, "wip"), 							_t = "WIP")
								doc.li().a(href = os.path.join("/", self.config.tgtsubdir, "articles"), 						_t = "Articles")
								doc.li().a(href = os.path.join("/", self.config.tgtsubdir, "contact.html"), 					_t = "Contact")
								doc.li().a(href = os.path.join("/", self.config.tgtsubdir, "about.html"), 					_t = "About")
								doc.li().a(klass = 'highlightnav', href = os.path.join("/", self.config.tgtsubdir, "shop"),	_t = "Shop")
				with doc.main():
					# embed the body of the document here
					body(doc)

				# spacer to force the footer down
				#doc.div(klass = "vertspacer")

				with doc.footer():
					doc.section().p(_t = f"Content &copy; {self.config.current_year} Vigilante Sculpting")
					with doc.ul(klass = "links"):
						doc.li().a(href="https://mastodon.social/@gorb314", 		_t = "Mastodon")
						doc.li().a(href="https://www.artstation.com/g0rb", 			_t = "ArtStation")
						doc.li().a(href="https://www.deviantart.com/gorb", 			_t = "DeviantArt")
						doc.li().a(href="https://www.reddit.com/user/gorb314", 		_t = "Reddit")
						doc.li().a(href="https://instagram.com/gorb314", 			_t = "Instagram")
						doc.li().a(href="https://www.puttyandpaint.com/g0rb",	 	_t = "Putty & Paint")
						doc.li().a(href="http://www.coolminiornot.com/artist/gorb", _t = "CMON")
					with doc.a(href = os.path.join("/", self.config.tgtsubdir)):
						doc.div(klass = "titleimage").img(id = "titleimage", src = os.path.join("/", self.config.tgtsubdir, "images", "logo.png"))
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
						with doc.a(href = post[source], rel="syndication", klass="u-syndication"):
							doc(f"{name}")
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
						with doc.a(href = post[place], rel="syndication", klass="u-syndication"):
							doc(f"{name}")
		return doc

	def postsummary(self, doc, postpath, post):
		postlink = os.path.join("/", self.config.tgtsubdir, f"{post.slug}.html")
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
			doc(f"{self.truncate(post.content)}&nbsp;")
		with doc.p(klass = "more").a(klass = "more", href = postlink):
			doc("Read more")
		return doc

	def makeslides(self, doc, postpath, posts):
		with doc.section(klass = "slides"):
			for post in posts:
				with doc.div(klass = "slide"):
					self.postsummary(doc, postpath, post)

	# ---------------------------------------------------------------------
	#  Create the main index.html
	# ---------------------------------------------------------------------

	def mainindex(self, ):
		def body(doc):
			with doc.section(klass = "mainsection"):
				with doc.p():
					doc("Welcome to Vigilante Sculpting. This is where I post my sculpting, scratchbuilding, drawing and paintig work.")

			def mainslidesection(path, postpath, title, rsstitle, posts, readmoretext):
				with doc.section(klass = "mainsection"):
					with doc.div(klass = "postnav"):
						with doc.a(href = path).h1():
							doc(title)
						with doc.a(href = os.path.join("/", self.config.tgtsubdir, postpath, "rss.xml")):
							doc.div(klass = "postnav-right").img(src = os.path.join("/", self.config.tgtsubdir, "images/rss.png"), width = "32px", height = "32px", alt = rsstitle)
					self.makeslides(doc, postpath, posts)
					with doc.p().a(href = path):
						doc(f"{readmoretext} &#x300B;")
			mainslidesection('blog',	 'blog',	 'Latest News',						'News RSS Feed',	 self.content.sortedblogposts[:3], 'Read latest news on the blog')
			mainslidesection('projects', 'projects', 'Latest Projects',					'Projects RSS Feed', self.content.sortedprojects[:3],  'See more finished projects')
			mainslidesection('sketches', 'sketches', 'Latest Sketches &amp; Drawings', 	'Sketches RSS Feed', self.content.sortedsketches[:3],  'See more sketches &amp; drawings')
			mainslidesection('articles', 'articles', 'Latest Articles',					'Articles RSS Feed', self.content.sortedarticles[:3],  'Read more articles')

			def maintextsection(path, title, subtitle):
				with doc.section(klass = "mainsection"):
					with doc.a(href = path).h2():
						doc(title)
					with doc.p().a(href = path):
						doc(subtitle)

			maintextsection('contact.html', 'Contact me', 'Get in touch...')
			maintextsection('about.html', 'About me', 'Read more about this site and myself here...')

		return self.page(title = 'Home', body = body) # base_path = '', meta = ''


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
			doc.p(_t = "This post has been tagged with")
			with doc.ul(klass = "posttags"):
				for tag in tags:
					with doc.li(klass = "taglink").a(href = os.path.join("/", "tags", f"{self.slugify(tag)}.html")):
						doc(tag)

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
				doc.h1(_t=post.title)
				with doc.p(klass = "meta"):
					doc(f"Published on {datetime.datetime.strftime(post.date, '%d/%m/%Y @%H:%M:%S')} by <b>{post.author}</b>")
				with doc.section(klass = "mainsection"):
					doc(post.content)
				self.originalpost(doc, post)
				self.posttags(doc, post.tags)
				#doc.div(klass="vertspacer")
			self.postnavigation(doc, postid, posts, 'post')
			if "comments" in post:
				self.comments(doc, post.comments)
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
		return [items[i*groupsize : i*groupsize + groupsize] for i in range(1 + len(items)//groupsize)]

	def indexpage(self, pageid, postgroup, pagecount, title, targetdir, postsdir, description):
		def body(doc):
			with doc.div(klass = "postnav"):
				with doc.div():
					doc.h1(_t = title)
					if pagecount > 1:
						doc.h3(_t = f"Page {pageid + 1}/{pagecount}")
				with doc.a(href = os.path.join("/", self.config.tgtsubdir, targetdir, "rss.xml")):
					doc.div(klass = "postnav-right").img(src = os.path.join("/", self.config.tgtsubdir, "images/rss.png"), width = "32px", height = "32px", alt = f"{title} RSS Feed")
			self.paginatenavigation(doc, pageid, pagecount, "index")
			with doc.article():
				doc.p(_t = description)
				self.makeslides(doc, postsdir, postgroup)
				#doc.div(klass = "vertspacer")
			self.paginatenavigation(doc, pageid, pagecount, "index")
		return self.page(title = title, body = body)


	def projectpost(self, projectid, pagecount, project, postgroupid, postgroup):
		def meta(doc):
			# doc.link(rel="alternate", type="application/rss+xml", title=f"Comments on '{project.title} - {self.config.title}'", href=commentpath)
			pass
		def body(doc):
			with doc.article():
				self.postnavigation(doc, projectid, self.content.sortedprojects, "project")

				if postgroupid == 0:
					doc.h1(_t = project.title)
					doc.p(klass = "meta", _t = f"Published on {datetime.datetime.strftime(project.date, '%d/%m/%Y @%H:%M:%S')} by <b>{project.author}</b>")
					with doc.section(klass = "mainsection"):
						doc(project.content)
					self.posttags(doc, project.tags)

				if len(postgroup) > 0:
					with doc.section(klass = "stepxstep"):
						if len(postgroup) > 1:
							doc.h2(_t = f"Step by step (Steps {postgroupid*self.config.paginatecount + 1} thru {postgroupid*self.config.paginatecount + len(postgroup)} of {len(project.posts)})")
						doc.p(_t = "These are the posts I made during the making of this project, in chronological order")
						self.paginatenavigation(doc, postgroupid, pagecount, project.slug)
						self.makeslides(doc, "../blog", postgroup)
						self.paginatenavigation(doc, postgroupid, pagecount, project.slug)

				self.postnavigation(doc, projectid, self.content.sortedprojects, "project")
			if "comments" in project:
				self.comments(doc, project.comments)
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

				doc.h1(_t = f"Posts tagged with '{tag.name}'")

				if pagecount > 1:
					doc.h3(_t = f"Page {pageid + 1} of {pagecount}, with {len(tag.posts)} posts")
				else:
					doc.h3(_t = f"{len(tag.posts)} posts")

				with doc.table(klass = "tagtable"):
					for post in postgroup:
						postlink = os.path.join("/", self.config.tgtsubdir, f"{post.slug}.html")
						with doc.tr():
							with doc.td(rowspan = 2, klass = "tagicon"):
								if "icon" in post:
									with doc.a(href = postlink):
										doc.img(src = post.icon, loading = "lazy", klass="iconthumbnail")
							with doc.td(klass = "tagtitle"):
								with doc.a(href = postlink):
									doc(post.title)
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

		self.output(self.mainindex(), "index.html")
		self.output(self.about(), "about.html")
		self.output(self.contact(), "contact.html")

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
			for postgroupid, postgroup in enumerate(postgroups):
				pagenum = postgroupid if postgroupid > 0 else ""
				filename = os.path.join(f"{project.slug}{pagenum}.html")
				self.output(self.projectpost(projectid, pagecount, project, postgroupid, postgroup), filename)
			
