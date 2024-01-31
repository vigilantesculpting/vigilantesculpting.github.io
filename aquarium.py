#!/usr/bin/env python3

""" aquarium is an html generator

It uses python's special methods (__getattr__, __call__, __enter__ and __exit___) to implement
a framework for easily composing html inside python itself.
Instead of using a string template that embeds python, this embeds the string template into python.

This code

import aquarium
doc = aquarium.Doc()
with doc.html(lang = "en"):
	with doc.header():
		doc.meta(charset = "utf-8")	
	with doc.body():
		doc.p("Hello world!")
print(doc)

will output a simple valid HTML5 webpage:
<!DOCTYPE html>
<html lang='en'>
  <header>
    <meta charset='utf-8' />
  </header>
  <body>
    <p>Hello world!</p>
  </body>
</html>

Using the with-clause, we can make enclosing tags. Using chaining, we can embed tags.
Inner text is added by simply calling an enclosing tag with an unnamed text argument.
Keyword arguments are converted into tag attributes.

So for example the following code snippet

with doc.section(klass = "navbar").ul():
	for i, (name, url) in enumerate(navitems):
		doc.li(klass = "active") if i == activenavitem else "").a(name, href = url)

might procuce the following:

<section class='navbar'>
  <ul>
    <li class=''>
      <a href='/'>Home</a>
    </li>
    <li class='active'>
      <a href='/about.html'>About</a>
    </li>
    <li class=''>
      <a href='/contact.html'>Contact</a>
    </li>
  </ul>
</section>

depending on the contents of navitems and activenavitem.

Aquarium is heavily inspired by airium, a python to HTML and HTML to python generator.
While Aquarium cannot convert HTML back into a valid aquarium script, it does generate HTML
about twice as fast as airium does.

"""

class Text:

	""" A simple piece of text, embedded inside an enclosing tag
	It is created by either calling a Doc or Tag instance with an unnamed argument.
	For example, 
		doc("hello world!")
	creates and adds a "hello world!" Text to the document.
	Similarly, doc.p("hello world!") adds a "hello world!" text embedded in a <p>aragraph tag.
	An initial Text tag is (mis)used by a Doc as a doctype element.
	Text elements are terminal: they cannot have children. This class therefore does not
	override the special __call__, __getattr__ or __enter__ / __exit__ methods.
	"""

	def __init__(self, doc, content: str):
		self.doc = doc
		self.content = content

	# Generate

	def text(self, lb, level:int = 0) -> str:
		return str(self.content)

	# Debug

	def struct(self, level:int = 0) -> str:
		print(self.doc.indent(level) + f"Text<{self.content}>")


class Tag:

	""" A tag element. Tags can be nested. Typically, a document has one root tag.
	Tags are created by using the Doc's __getattr__ special method.
	A Tag can have tag attributes added by adding keyword arguments to its __call__.
	Chaining tags will create a hierarchy, since the Tag class also overrides its __getattr__
	special method to create enclosed child tags.
	The Tag class also overrides __enter__ and __exit__, so that tags can be used in a with-clause
	to create an enclosed section.
	"""

	def __init__(self, doc, parent, tagname: str):
		#print(f"new Tag({doc}, {parent}, {tagname})")
		self.doc = doc
		self.parent = parent
		self._tagname = tagname
		self.children = []
		self._params = {}
		self.deferred = False
		self.chain = None

	# Compose

	def __call__(self, _t = None, *args, **kwargs):
		if _t is not None:
			self.children.append(Text(self.doc, _t))
		else:
			for arg in args:
				self.children.append(Text(self.doc, arg))
		self._params.update(kwargs)
		return self

	def __getattr__(self, tagname):
		tag = Tag(self.doc, self, tagname = tagname)
		self.doc.current.children.append(tag)
		self.doc.current = tag
		# continue the current chain
		tag.chain = self
		return tag

	def __enter__(self):
		# start a deferred chain
		self.deferred = True
		return self

	def __exit__(self, *args):
		# first unchain any existing chain(s)
		while self.doc.current != self:
			self.doc.unchain()
		assert(self.doc.current == self)
		# now unchain this chain
		self.doc.unchain()

	# Generate

	def param(self, key, value):
		""" Generates a single tag attribute and its value
		"""
		return f"{self.doc.attrname(key)}='{value}'"

	def params(self):
		""" Generates all of the tag attribute/value pairs for this Tag.
		"""
		params = " ".join([self.param(key, value) for (key, value) in self._params.items()])
		return "" if params == "" else " " + params

	def opentag(self) -> str:
		""" Generates the opening tag (plus attributes) for this Tag
		"""
		return f"<{self.doc.tagname(self._tagname)}{self.params()}>"
	def closetag(self) -> str:
		""" Generates the closing tag for this Tag
		"""
		return f"</{self.doc.tagname(self._tagname)}>"
	def openclosetag(self) -> str:
		""" Generates an open and closed tag for this Tag
		"""
		if self.doc.single_tag(self._tagname):
			# since the tag can be a single tag, we create a <tag key='value'... /> string
			return f"<{self.doc.tagname(self._tagname)}{self.params()} />"
		else:
			# the tag is not a singletag, so create the typical <tag key='value'...></tag> pair
			return self.opentag() + self.closetag()

	def text(self, lb, level:int = 0) -> str:
		""" Generates the tag, along with its attributes and enclosed inner HTML, at the appropriate indentation level, using the specified linebreak character
		"""
		indent = self.doc.indent(level)
		if len(self.children) == 0:
			return indent + self.openclosetag()
		elif len(self.children) == 1 and type(self.children[0]) == Text:
			# since the tag has only one Text element, we do not use the linebreak character but instead generate a single line,
			# eg. <tag key='value'...>text</tag>
			return indent + self.opentag() + self.children[0].text(lb, 0) + self.closetag()
		else:
			return indent + self.opentag() + lb + lb.join([child.text(lb, level + 1) for child in self.children]) + lb + indent + self.closetag()

	# Debug

	def struct(self, level:int = 0):
		print(self.doc.indent(level) + f"<{self.doc.tagname(self._tagname)}{self.params()}>: {'chainstart' if self.chain is None else ''} {'deferred' if self.deferred else ''}")
		for child in self.children:
			child.struct(level + 1)


class Doc:

	""" The Doc class represents a document

	It has a number of children, these can be Tags or Texts.
	Typically, an html document will have a single Text child (representing the doctype string), followed by a single Tag html child.
	The html Tag child will have a head Tag child and a body Tag child.
	
	The Doc maintains a current Tag element, to which additional Tags / Texts are appended.
	The Doc stores chained state by initialising each individual chain of tags, and properly escapes and collapses these at the end
	of chains and with-clauses.
	"""

	def __init__(self, 
			doctype:str = None, 
			base_indent:str = '\t', 
			current_level:int = 0, 
			source_minify:bool = False, 
			source_line_break_character:str = '\n'
			):
		""" Creates a new document

		The default doctype string is for html documents. If not None, a Text instance with that string is added as a first child.
		The document can have an initial indentation level (default is 0), and is by default indented with multiples of the base_indent string.
		The generated code uses the source_line_break_character to break lines in the output.
		If source_minify is True, no indentation and linebreaking is done.
		""" 
		#print(f"new Doc({doctype})")
		# for example, source_minify = True?
		self.children = []
		self.current = None
		if doctype is not None:
			self.children.append(Text(self, doctype))
		self.base_indent = base_indent
		self.current_level = current_level
		self.source_minify = source_minify
		self.source_line_break_character = source_line_break_character

	# Compose

	def __call__(self, content:str) -> Text:
		""" Creates a new Text instance, as in
			doc("hello world!")
		"""
		text = Text(self, content)
		if self.current is None:
			self.children.append(text)
		else:
			self.current.children.append(text)
		return text

	def __getattr__(self, tagname:str) -> Tag:
		""" Creates a new Tag instance, as in
			doc.div()
		"""
		# check, is this attribute in our 
		#print()
		#print(f"__getattr__({tagname})")
		# eg doc.html(...)...
		# we are creating a new chain. First collapse the old chain
		if self.current is not None:
			if not self.current.deferred:
				# the current chain is not deferred, so unchain it and start a new one
				self.unchain()
		tag = Tag(self, self.current, tagname = tagname)
		if self.current is None:
			self.children.append(tag)
		else:
			self.current.children.append(tag)
		self.current = tag
		#print(f"new chain at {tag} started")
		return tag

	# Generate

	def text(self) -> str:
		""" Outputs the document
		This determines the linebreak character to use, and outputs all children starting at the current identation level
		"""
		lb = "" if self.source_minify else self.source_line_break_character
		return lb.join([child.text(lb, self.current_level) for child in self.children])

	def __repr__(self) -> str:
		return self.text()

	# Implementation

	def unchain(self):
		# we need unchain this chain
		while self.current.chain is not None:
			self.current = self.current.parent
		self.current = self.current.parent

	def indent(self, level):
		if self.source_minify:
			return ""
		return self.base_indent * level

	tag_substitutes = {}
	def tagname(self, name:str) -> str:
		return self.tag_substitutes.get(name, name)

	attr_substitutes = {}
	def attrname(self, name:str) -> str:
		return self.attr_substitutes.get(name, name)

	single_tags = set([])
	def single_tag(self, name:str) -> bool:
		return name in self.single_tags

	# Debug

	def struct(self):
		print(f"Doc<>")
		for child in self.children:
			child.struct()


class Html(Doc):

	def __init__(self, 
			doctype:str = "<!DOCTYPE html>", 
			base_indent:str = '  ', 
			current_level:int = 0, 
			source_minify:bool = False, 
			source_line_break_character:str = "\n"
			):
		super(Html, self).__init__(doctype, base_indent, current_level, source_minify, source_line_break_character)

		self.tag_substitutes = {
			'del_': 		'del',
		}

		self.attr_substitutes = {
			'klass': 'class',
			'async_': 'async',
			'for_': 'for',
			'in_': 'in',

			# from XML
			'xmlns_xlink': 'xmlns:xlink',

			# from SVG ns
			'fill_opacity': 'fill-opacity',
			'stroke_width': 'stroke-width',
			'stroke_dasharray': ' stroke-dasharray',
			'stroke_opacity': 'stroke-opacity',
			'stroke_dashoffset': 'stroke-dashoffset',
			'stroke_linejoin': 'stroke-linejoin',
			'stroke_linecap': 'stroke-linecap',
			'stroke_miterlimit': 'stroke-miterlimit',

			# you may add translations to this dict after creating the Airium instance:
			# a = Airium()
			# a.ATTRIBUTE_NAME_SUBSTITUTES.update({
			#   # e.g.
			#   'clas': 'class',
			#   'data_img_url_small': 'data-img_url_small',
			# })
		}

		self.single_tags = set([
			# You may change this list after creating the Airium instance by overriding it, like this:
			# a = Airium()
			# a.SINGLE_TAGS = ['hr', 'br', 'foo', 'ect']
			# or by extend or append:
			# a.SINGLE_TAGS.extend(['foo', 'ect'])
			# You can also change the class itself, ie.
			# Airium.SINGLE_TAGS.extend(...)
			# This change will persist across all files that use airium in a single project
			'input', 'hr', 'br', 'img', 'area', 'link',
			'col', 'meta', 'base', 'param', 'wbr',
			'keygen', 'source', 'track', 'embed',
		])

class Rss(Doc):

	def __init__(self, 
			doctype:str = "<?xml version='1.0' encoding='UTF-8'?>", 
			base_indent:str = '  ', 
			current_level:int = 0, 
			source_minify:bool = False, 
			source_line_break_character:str = "\n"
			):
		super(Rss, self).__init__(doctype, base_indent, current_level, source_minify, source_line_break_character)

		self.tag_substitutes.update({
				'_tags__taglist': 'tags:taglist',
				'_tags__tag': 'tags:tag',		
			})
		self.attr_substitutes.update({
				'_xmlns__tags': 'xmlns:tags',
				'_xmlns__conversation': 'xmlns:conversation',
			})







if __name__ == "__main__":
	doc = Html()

	with doc.body():
		with doc.main():
			with doc.nav():
				with doc.section(klass = "titlesection"):
					with doc.a(href = "/"):
						doc.div(klass = "titleimage").img(id = "titleimage", src = "/images/title.png")
					with doc.div(klass = "sitenavigation"):
						#with doc.span("home").a(os.path.join("/", self.config.tgtsubdir)):
						#	doc("Home")
						with doc.ul(klass = "links"):
							doc.li().a(href = "", 								_t = "Home")
							doc.li().a(href = "blog", 							_t = "Blog")
							doc.li().a(href = "projects", 						_t = "Projects")
							doc.li().a(href = "sketches", 						_t = "Sketches")
							doc.li().a(href = "articles", 						_t = "Articles")
							doc.li().a(href = "contact.html", 					_t = "Contact")
							doc.li().a(href = "about.html", 					_t = "About")
			with doc.article():
				doc.p("The article...")


#	with doc.html(lang="en"):
#		with doc.head():
#			pass
#		with doc.body():
#			doc.p("head")
#			with doc.a(href="url"):
#				doc.p("hello world")
#			doc.p("foot")

#		with doc.body():
#			doc.p(_t = "hello world")
#			doc.a(href="http://blah").h1(_t = "blah")
#			doc.p(_t = "footer")

	print(doc.struct())
	print(doc.text())

	doc = Doc()
	navitems = [("Home", "/"), ("About", "/about.html"), ("Contact", "/contact.html")]
	activenavitem = 1
	with doc.section(klass = "navbar").ul():
		for i, (name, url) in enumerate(navitems):
			doc.li(klass = "active" if i == activenavitem else "").a(name, href = url)

	print(doc)








