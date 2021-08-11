#!/usr/bin/env python

"""solon is a text template rendering engine in Python

	It aims to add conditional, looping and composition to text files, specifically aimed at but not limited to generating HTML from templates. 

	It uses simple markers to embed its code, and uses [pretzyl](https://github.com/vigilantesculpting/pretzyl)
	for the evaluation of statements in conditionals and as text replacement / filtering.

	solon can define pieces of text as functions, and can call these to either replace or wrap a specific piece of text,
	passing arguments to the called function. One template can import another, which makes all definitions in the
	importee available in the importer, and adds any output text from the importee at the point of import in the importer.

"""

"""
Implementation:

solon.Solon is the main interface class to solon.
It holds 4 other class instances that do the heavy lifting:
- solon.Context: this holds a stack of environments (NSDicts in this case), which act as variable storage.
	It provides all the other instances a way to communicate and extract data from the outside world, and acts
	as a receptacle for data that the instances produce.
- pretzyl.Pretzyl: this implements the pretzyl stack-based expression language.
	All expression logic in solon is implemented as pretzyl expressions.
	This instance is available as a tokenizer to the parser, and an evaluator to the renderer.
	It uses the context to extract and process data
- solon.Parser: parses template texts into node trees, that are stored in the context.
	The nodes in the tree are preprocessed, so that their pretzyl expressions are available as token lists.
	Syntax checking is done as much as possible.
- solon.Renderer: renders a node tree, using a given context and the pretzyl parser as expression evaluator.
	Runtime error checking is done as much as possible.

Finally, the solon.Node class is used to represent parsed templates. A node tree is produced by the parser.
The renderer acts as a visitor, and visits each node in a depth-first fashion to render the resulting text.
As such, the node tree acts as a communication between the parser and the renderer.
"""

import sys
import re
import os

import pretzyl
import nsdict

# internal debugging
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
	pretzyl.setlog(level - 1)
	nsdict.setlog(level - 1)


#######################################################################
#
# Solon
#

class Solon:
	"""The main Solon interface class.
	"""

	def __init__(self, vars = {}):
		self.context = Context(vars)
		self.pretzyl = pretzyl.Pretzyl(self.context)
		self.parser = Parser(self.context, tokenizer = self.pretzyl)
		self.renderer = Renderer(self.context, evaluator = self.pretzyl)

	def addtemplate(self, name, text):
		"""This method adds the named piece of text as a template to the current environment,
		by running it through the parser to produce a Node
		"""
		self.context[name] = self.parser.parsetext(name, text)

	def rendertemplate(self, name, keepWhitespace=False, keepComments=False):
		"""This is the main entry point to rendering a named template
		The template node is found in the environment using the given name as reference.
		"""
		return self.renderer.rendernode(self.context[name], keepWhitespace, keepComments)


#######################################################################
#
# Node tree
#

class Node:
	"""This class implements a node of execution.

	It is a tree structure: the root node of the tree has no parent.
	Nodes that represent solon line commands have no children.
	Nodes that represent solon block commands can have children.

	It is the abstract syntax tree implementation for solon.
	"""
	def __init__(self, name, line="", parent = None, filename = "", linenr = -1):
		"""A node knows what source line / line number created it
		"""
		self.name = name
		self.line = self.parse(line)
		self.parent = parent
		self.children = []
		self.args = []
		self.filename = filename
		self.linenr_ = linenr

	def path(self):
		"""Returns the full path of the node, by looking at its parent nodes.
		"""
		if self.parent is not None:
			return os.path.join(self.parent.path(), self.name)
		else:
			return self.name

	def linenr(self):
		"""Returns the line number where the node was created from.
		"""
		return self.linenr_

	def parse(self, line):
		if self.name == "text":
			return line
		else:
			values = line.strip().split(" ", 1)
			if len(values) > 1:
				return values[1]
			else:
				return ""

	def append(self, name, line, filename, linenr):
		self.children.append(Node(name, line, self, filename, linenr))
		return self.children[-1]

	def push(self, name, line, filename, linenr):
		self.children.append(Node(name, line, self, filename, linenr))
		return self.children[-1]

	def pop(self):
		return self.parent



#######################################################################
#
# Parser
#



class Parser:

	def __init__(self, context, tokenizer):
		self.context = context
		self.tokenizer = tokenizer

	# single line node directives
	comment_re 	= re.compile(r"\%#.*$")
	comment2_re = re.compile(r"\%-.*$")
	import_re 	= re.compile(r"\%import\s+.*$")
	call_re 	= re.compile(r"\%call\s+.*$")
	embed_re 	= re.compile(r"\%embed\s*?(\s+(.+))?$")
	set_re 		= re.compile(r"\%set\s+.*$")
	# block node directives
	for_re 		= re.compile(r"\%for\s+.*$")
	if_re  		= re.compile(r"\%if\s+.*$")
	elif_re		= re.compile(r"\%elif\s+.*$")
	else_re		= re.compile(r"\%else\s*$")
	output_re 	= re.compile(r"\%output\s+.*$")
	wrap_re 	= re.compile(r"\%wrap\s+.*$")
	func_re 	= re.compile(r"\%func\s+.*$")
	write_re 	= re.compile(r"\%write\s+.*$")
	# block node terminator
	end_re 		= re.compile(r"\%end\s*$")
	# block node control flow
	exit_re 	= re.compile(r"\%exit\s*$")
	skip_re 	= re.compile(r"\%skip\s*$")
	halt_re 	= re.compile(r"\%halt\s*$")

	DELIMITER = "%"
	COMMENT = "#-"

	def creatematchlists(self, n):
		"""Parses a line that should look like "<expression>: <expression>"
		Because an expression can be quite hard to parse, we first tokenize it, then check for the single
		required ":" token, then split the two lists of expressions and return them.

		This function is always executed during the PARSE phase, so all errors are SyntaxErrors
		"""
		tokens = self.tokenizer.tokenize(n.line, specialchars = ":")
		seperatorcount = tokens.count(pretzyl.Reference(":"))
		if seperatorcount != 1:
			# we need one ":", and one only, to separate the parameters from the expression.
			raise SyntaxError("match expression [%s] is missing colon separator in node [%s] from %s@%i" % (n.line, n.name, n.path(), n.linenr()))
		separatorindex = tokens.index(pretzyl.Reference(":"))
		leftlist, rightlist = tokens[:separatorindex], tokens[separatorindex+1:]
		# the left and right lists now contain macro expanded converted References and Literals, ready to be used
		# to either evaluate or assign to stuff
		log("creatematchlists: line [%s] -> left [%s] right [%s]" % (n.line, leftlist, rightlist))
		return leftlist, rightlist

	def checkparams(self, tokenlist):
		"""This takes a tokenized converted list, and makes sure it is a simple list of references
		"""
		for token in tokenlist:
			if not isinstance(token, pretzyl.Reference):
				# we do not allow literals in param lists
				raise SyntaxError("bad parameter [%s] in parameter list: [%s]" % (token, tokenlist))
			if token.name in (pretzyl.PUSHTOKEN, pretzyl.POPTOKEN):
				# we do not allow brackets in param lists (yet)
				raise SyntaxError("bad parameter [%s] in parameter list expr: [%s]" % (token.name, tokenlist))
		return True

	def parseloop(self, n):
		"""Extracts the parameters for a loop expression.
		The Expression must looks like "<expression>: <expression>""
		The left list forms the named parameters for each iteration of the loop, and
		the right list forms the list of arguments.
		The list will be executed for each resulting set of args after the arguments have been evaluated
		"""
		n.paramlist, n.arglist = self.creatematchlists(n)
		log("%for: ", n.paramlist, " => ", n.arglist)

		# params must be a simple list of references
		self.checkparams(n.paramlist)
		if len(n.paramlist) == 0:
			raise SyntaxError("empty paramlist in for [%s] invalid in node [%s] from %s@%i" % (n.line, n.name, n.path(), n.linenr()))

	def parsefunc(self, n):
		"""Creates a function call node and its environment from a %call line, with "<expression>: <expression>"
		The left expression should evaluate to the function node.
		The right expression should evaluate to a set of arguments, which can be matched up to the function node's
		parameters.
		"""
		n.namelist, n.arglist = self.creatematchlists(n)

		if len(n.namelist) != 1:
			# we need one name for the function
			raise SyntaxError("for expression [%s] is invalid in node [%s] from %s@%i" % (n.line, n.name, n.path(), n.linenr()))
		self.checkparams(n.namelist)

	def parseline(self, line):
		"""Parses a line of solon template

		Lines in the text are parsed sequentially.
		Each line can be of the form "[TEXT] [COMMAND] [COMMENT]", with each piece being optional.
		The main delimiter is the percentage sign "%". It can be escaped by doubling up, ie "%%"

		A command starts with the first bare "%" found.
		A comment starts with a "%-" or "%#".

		Once a command starts, the rest of the line will be part of the command, until a comment
		starts, after which the rest of the line is part of the comment.
		"""
		text = None
		command = None
		comment = None

		items = [item for item in re.split("(" + self.DELIMITER + ")", line) if item]
		#print "\t::", items
		if len(items) > 0:
			# if the line is not split, then there are no %s, which means it is all text
			if len(items) == 1:
				text = line.rstrip()
			else:
				commentstart = None
				commandstart = None
				a = items[0]
				D = enumerate(items[1:])
				try:
					while True:
						i, b = D.next()
						if a == self.DELIMITER:
							if b == self.DELIMITER:
								# escaped %
								i, b = D.next()
								a = b
								continue
							if b.startswith(self.COMMENT[0]) or b.startswith(self.COMMENT[1]):
								# comment
								commentstart = i
								break
							commandstart = i
						a = b
				except StopIteration:
					pass
				if commentstart is not None:
					items, comment = items[:commentstart], "".join(items[commentstart:])
					comment = comment.replace(self.DELIMITER*2, self.DELIMITER).rstrip()
				if commandstart is not None:
					items, command = items[:commandstart], "".join(items[commandstart:])
					command = command.replace(self.DELIMITER*2, self.DELIMITER).rstrip()
				string = "".join(items)
				string = string.replace(self.DELIMITER*2, self.DELIMITER).rstrip()
				if len(string) > 0:
					text = string
		else:
			text = "" # empty string
				
		return text, command, comment


	def parsetext(self, name, text):
		"""The main parsing method: parses a text into a hierarchical Node template

		Each command's expression is evaluated and pretzyl code is tokenized here.
		"""
		root = Node(name, "", None, name, 0)
		current = root
		for linenr_, line in enumerate(text.split("\n")):

			linenr = linenr_ + 1 # we naturally count lines starting at 1

			text, command, comment = self.parseline(line)

			# the line is now split into text, command and comment parts.
			# any of these may be empty, in which case they are ommitted

			log("line [%s] => [%s] [%s] [%s]" % (line, text, command, comment))

			if text is not None:
				log("\tline [%s] matches 'text'" % text)
				if current.name == "text":
					# simply append the line to the current statemnt
					current.line += "\n" + text
				else:
					current.append("text", text, name, linenr)

			if command is not None:
				if self.import_re.match(command):
					log("\tline [%s] matches 'import'" % command)
					n = current.append("import", command, name, linenr)
					n.tokens = self.tokenizer.tokenize(n.line)

				elif self.call_re.match(command):
					log("\tline [%s] matches 'call'" % command)
					n = current.append("call", command, name, linenr)
					self.parsefunc(n)

				elif self.embed_re.match(command):
					log("\tline [%s] matches 'embed'" % command)
					n = current.append("embed", command, name, linenr)
					if len(n.line) == 0:
						n.tokens = self.tokenizer.tokenize('__embed__')
					else:
						n.tokens = self.tokenizer.tokenize(n.line)

				elif self.set_re.match(command):
					log("\tline [%s] matches 'set'" % command)
					n = current.append("set", command, name, linenr)
					n.namelist, n.expressionlist = self.creatematchlists(n)
					# TODO: make the name an expression, so that we can have dynamic names
					if len(n.namelist) != 1:
						raise SyntaxError("set expression [%s] has invalid name in node [%s] from %s@%i" % (n.line, n.name, n.path(), n.linenr()))

				elif self.for_re.match(command):
					log("\tline [%s] matches 'for'" % command)
					current = current.push("for", command, name, linenr)
					self.parseloop(current)

				elif self.if_re.match(command):
					log("\tline [%s] matches 'if'" % command)
					current = current.push("if", "", name, linenr)
					current = current.push("ifthen", command, name, linenr)
					current.predtokens = self.tokenizer.tokenize(current.line)

				elif self.elif_re.match(command):
					log("\tline [%s] matches 'elif'" % command)
					current = current.pop()
					assert(current.name == "if")
					current = current.push("ifthen", command, name, linenr)
					current.predtokens = self.tokenizer.tokenize(current.line)

				elif self.else_re.match(command):
					log("\tline [%s] matches 'else'" % command)
					current = current.pop()
					assert(current.name == "if")
					current = current.push("ifthen", "ifthen True", name, linenr)
					current.predtokens = self.tokenizer.tokenize(current.line)

				elif self.output_re.match(command):
					log("\tline [%s] matches 'output'" % command)
					current = current.push("output", command, name, linenr)
					current.tokens = self.tokenizer.tokenize(current.line)

				elif self.wrap_re.match(command):
					log("\tline [%s] matches 'wrap'" % command)
					current = current.push("wrap", command, name, linenr)
					self.parsefunc(current)

				elif self.func_re.match(command):
					log("\tline [%s] matches 'func'" % command)
					current = current.push("func", command, name, linenr)
					n = current
					n.namelist, n.paramlist = self.creatematchlists(n)
					if len(n.namelist) != 1:
						# we need one name for the function
						raise SyntaxError("func expression [%s] is invalid in node [%s] from %s@%i" % (n.line, n.name, n.path(), n.linenr()))
					self.checkparams(n.namelist)
					self.checkparams(n.paramlist)
					n.params = n.paramlist
					self.context[n.namelist[0].name] = n

				elif self.write_re.match(command):
					log("\tline [%s] matches 'write'" % command)
					current = current.push("write", command, name, linenr)
					current.tokens = self.tokenizer.tokenize(current.line)

				elif self.end_re.match(command):
					log("\tline [%s] matches 'end'" % command)
					if current.parent is None:
						n = current
						raise SyntaxError("unexpected %%end in node [%s] from %s@%i" % (n.line, n.path(), n.linenr()))
					current = current.pop()
					if current.name == "if":
						assert(current.parent is not None)
						current = current.pop()
					assert(current is not None)

				elif self.exit_re.match(command):
					log("\tline [%s] matches 'exit'" % command)
					current.append("exit", command, name, linenr)

				elif self.skip_re.match(command):
					log("\tline [%s] matches 'skip'" % command)
					current.append("skip", command, name, linenr)

				elif self.halt_re.match(command):
					log("\tline [%s] matches 'halt'" % command)
					current.append("halt", command, name, linenr)

				else:
					raise SyntaxError("could not parse command [%s]" % command)

			if comment is not None:
				log("\tline [%s] matches 'comment'" % command)
				current.append("comment", comment, name, linenr)

		# check that we have closed all block node commands
		if current.parent is not None:
			c = current
			err = "Missing closing %ends:"
			while c.parent is not None:
				err += "\n\tnode [%s] from %s:%i" % (c.name, c.path(), c.linenr())
				c = c.parent
			raise SyntaxError(err)

		# post process the text to properly evaluate the the pretzyl expressions.
		self.processtext(root)
		return root

	def processtext(self, node):
		"""This processes the line in a text node by splitting the text into strings and pretzyl expressions.
		For example, the text
			hello {{world}}!
		will be split into
			[['hello'], [pretzyl.Reference('world')], ['!']]
		This allows for simple evaluation of each sublist, followed by a concatenation, to determine the rendered text later.
		"""
		if node.name == "text":
			n = node
			n.expr = []
			# break the line up into text and {{expressions}}
			starttext = 0
			while True:
				startexpr = n.line.find("{{", starttext)
				if startexpr == -1:
					n.expr.append([n.line[starttext:]])
					break
				n.expr.append([n.line[starttext:startexpr]])
				endexpr = n.line.find("}}", startexpr)
				if endexpr == -1:
					# error, must close!
					raise SyntaxError("missing }} on %s@%i" % (n.path(), n.linenr()))
				n.expr.append(self.tokenizer.tokenize(n.line[startexpr+2:endexpr]))
				starttext = endexpr+2
			log("converted text [%s] to items" % n.line, n.expr)
		else:
			# post process any children nodes:
			for child in node.children:
				self.processtext(child)



#######################################################################
#
# Renderer
#



class Renderer:

	def __init__(self, context, evaluator):
		self.context = context
		self.evaluator = evaluator

	def rendernode(self, node, keepWhitespace=False, keepComments=False):
		"""This is the main entry point to rendering a template node

		It calls rendernode_, which recurses down the tree of nodes.
		"""
		self.keepWhitespace = keepWhitespace
		self.keepComments = keepComments

		assert(len(self.context.vars) == 1)
		if "output" not in self.context:
			self.context["output"] = nsdict.NSDict()
		try:
			callstack = []
			result = self.rendernode_(node, callstack)
		except CommandException as e:
			result = e.result

		#assert(len(callstack) == 0)
		assert(len(self.context.vars) == 1)
		return result

	def genloopenv(self, node):
		"""Generates an env for every matchup in an evaluated "<expression>: <expression>"
		First we evaluate the argument list, to determine a set of arguments.
		Then each parameter is matched up with an item in the set of arguments, and the resulting
		env is yielded.
		There will be as many yields as the set of arguments allows.
		"""
		# arglist must be evaluated to produce a single list of arguments
		# arguments can be a regular list or a generator
		arguments = self.evaluatetokens(node.arglist)
		log("for: paramlist: ", node.paramlist, " arguments: ", arguments)

		# match up iterations of arguments to the set of parameters
		for i, args in enumerate(arguments):
			log("loop iteration %i with arguments " % i, args)
			env = {}
			if len(node.paramlist) == 1:
				log("paramlist size is 1, adding all args")
				# there is only one parameter, so it is assigned the entire argument for this iteration
				env[node.paramlist[0].name] = args
			else:
				log("paramlist size is >1, spreading all args")
				# there are multiple parameters, so assign each item in the iteration argument to a parameter
				# TODO: we should be able to get away with just the zip (and not the lengths), since generators
				# won't allow us to take the length until we convert to list...
				args = list(args)
				log("args is ", args)
				if len(node.paramlist) != len(args):
					raise RuntimeError("mismatched parameters/arguments in for loop iteration %i: [%s] from %s@%i" % (i, node.line, node.path(), node.linenr()))
				for param, arg in zip(node.paramlist, args):
					env[param.name] = arg
			yield env

	def createfuncenv(self, node):
		"""Creates a function call environment, from a match up of a set of parameters to a set of arguments
		"""
		functionnode = self.evaluatetokens(node.namelist)
		params = functionnode.params
		# callee must be a function Node
		if not isinstance(functionnode, Node):
			raise RuntimeError("Expected node, got [%s] instead" % type(functionnode))
		if functionnode.name != "func":
			raise RuntimeError("Expected [func] node, got [%s] node instead" % functionnode.name)

		# evaluate the argument list. We want all results as a list
		# typically we won't use a generator here, so we care about the list
		# TODO when pretzyl will evaluate all contents of lists before returning, we might be able to 
		# do away with returnall, but for now this suits.
		arguments = self.evaluatetokens(node.arglist, returnall=True)

		# match up the arguments to the set of parameters
		# As opposed to the loop env, we do NOT want to map a single function parameter to the entire
		# set of agruments. There should be a one-to-one mapping, and an error if this cannot be done.
		env = {}
		if len(params) == 0:
			if len(arguments) != 0:
				raise RuntimeError("func [%s] takes 0 argument (%i given)" % ((node.name), len(arguments)))
			# a parameterless function called with zero arguments is ok
		else:
			# params is greater than 0. Assign each param to a matching positional arg 
			# match up arg / param pairs
			if len(arguments) != len(params):
				raise RuntimeError("func [%s] takes %i arguments (%i given)" % (node.name, len(params), len(arguments)))
			for arg, param in zip(arguments, params):
				env[param.name] = arg
		return functionnode, env

	def rendernode_(self, node, callstack):
		"""Internal node rendering function.

		This evaluates the hierarchy of nodes, evaluating the pretzyl code in each node to determine
		the output of the node template.
		"""

		callstack.append(node)

		# some utility functions:
		def depth():
			return len(callstack)
			#return len(self.vars)
		def tabs():
			return "   "*depth()
		def llog(*args, **kwargs):
			if LOG: # try to short-cut logging calls as much as possible
				log(tabs(), *args, **kwargs)

		def rendernode_add(env, node, callstack):
			"""A utility function which pushes a new env on the stack,
			then renders the provided node in the new env, and finally pops
			the stack (adding the result from the node into the output),
			and returns the output.
			"""
			# we need to make sure that after the push happens, the pop happens.
			# this is done with finally, so any exception that comes through
			# keeps going, but no one ever leaves without popping the context.
			self.context.push(env)
			r = ""
			try:
				r = self.rendernode_(node, callstack)
			finally:
				self.context.pop(r)
			return r

		## The main loop

		llog("rendernode:", node.name)
		result = []

		try:
			for n in node.children:

				if n.name == "text":
					llog("resolving statemnt [%s]" % n.line)
					if len(n.expr) > 0:
						out = [str(self.evaluatetokens(expr)) for expr in n.expr]
						text = "".join(out)
						if len(text.strip()) > 0 or self.keepWhitespace:
							result.append(text)

				elif n.name == "comment":
					llog("resolving comment [%s]" % n.line)
					# TODO the following should probably not be in the environment, but a constructor argument
					#showcomments = 'config/showcomments' in self and self['config/showcomments']
					if self.keepComments:
						result.append("<!-- " + n.line + " -->")

				# calls rendernode
				# appends output
				# modifies current env
				elif n.name == "import":
					llog("resolving import [%s]" % n.line)
					# find the node to import:
					importednode = self.evaluatetokens(n.tokens)
					# this must be a node
					if not isinstance(importednode, Node):
						raise RuntimeError("importee [%s] is not a proper node %s@%i" % (n.line, n.path(), n.linenr()))				
					llog("importing ", importednode)
					# immediately render the node in this environment (no push!), as if it were at the same depth
					# note: this action may modify the current environment; this is a desired side-effect
					r = self.rendernode_(importednode, callstack)
					result.append(r)

				# appends var
				elif n.name == "embed":
					llog("resolving embed [%s]" % n.line)
					text = self.evaluatetokens(n.tokens)
					result.append(text)

				# calls rendernode in child env
				# appends output
				elif n.name == "for":
					llog("resolving for [%s]" % n.line)
					for env in self.genloopenv(n):
						output = ""
						try:
							output = rendernode_add(env, n, callstack)
						except SkipCommand as e:
							output = e.result
							# continue with the next iteration
							pass
						except ExitCommand as e:
							llog("caught ExitCommand in for loop, exiting the loop")
							output = e.result
							# append all output generated by the exiting node so far
							result.append(output)
							# exit the loop
							break
						# append all output generated by the exiting node so far
						result.append(output)

				# calls rendernode in child env
				# appends output
				elif n.name == "if":
					llog("resolving if [%s]" % n)
					for i in n.children:
						assert(i.name == "ifthen")
						llog("resolving ifthen [%s]" % i.line)
						# evaluate the predicate against the env:
						r = self.evaluatetokens(i.predtokens)
						llog("result is", r)
						if r:
							try:
								output = rendernode_add(None, i, callstack)
								result.append(output)
								break
								# exit on the first predicate that evaluated to True
							except CommandException as e:
								# catch and re-raise any command exceptions, so that halt, exit and skip don't get trapped here
								raise
							except RuntimeError as e:
								raise
							except EvaluationError as e:
								# See notes under "Exception chaining"
								raise EvaluationError(e, i), None, sys.exc_info()[2]
							except Exception as e:
								# See notes under "Exception chaining"
								raise EvaluationError(e, i), None, sys.exc_info()[2]

				# calls rendernode in child env, appends output
				elif n.name == "call":
					llog("resolving call [%s]" % n.line)
					# now get the wrapping function and its env
					try:
						functionnode, env = self.createfuncenv(n)
						# render the function node in the new environment:
						output = rendernode_add(env, functionnode, callstack + [n])
					except ExitCommand as e:
						llog("caught ExitCommand in call, exiting the function")
						output = e.result
					result.append(output)

				# calls rendernode in child env, appends output
				elif n.name == "wrap":
					llog("resolving wrap [%s]" % n.line)
					# first render the current node:
					wrapresult = rendernode_add(None, n, callstack)
					# now get the wrapping function and its env
					functionnode, env = self.createfuncenv(n)
					# enter the wrapresult in the function's env
					env['__embed__'] = wrapresult
					# finally render the wrapping function and add its result
					output = rendernode_add(env, functionnode, callstack)
					result.append(output)

				# modifies current env
				# embeds var
				elif n.name == "func":
					llog("resolving func [%s]" % n.line)
					# Note: so the effect here is that the header of a function is evaluated once only, and none of it is interpreted/parsed/executed.
					# So a function cannot change its name...
					# unless we do
					# 					name = self.evaluatetokens(namelist)
					# and then
					# 					self[name] = n

				# calls rendernode in child env
				# embeds output
				# modifies current env
				elif n.name == "write":
					llog("resolving write [%s]" % n.line)
					outputresult = rendernode_add(None, n, callstack)
					name = self.evaluatetokens(n.tokens)
					self.context[name] = outputresult

				# calls rendernode in child env
				# embeds output
				# modifies current env
				elif n.name == "output":
					llog("resolving output [%s]" % n.line)
					outputresult = rendernode_add(None, n, callstack)
					name = os.path.join('output', self.evaluatetokens(n.tokens))
					llog("output path: ", name, " -> ", len(outputresult), " characters")
					self.context[name] = outputresult

				# modifies current env
				# embeds var
				elif n.name == "set":
					llog("resolving set [%s]" % n.line)
					name = self.evaluatetokens(n.namelist)
					value = self.evaluatetokens(n.expressionlist)
					llog("setting name [%s] to value [%s]" % (name, value))
					self.context[name] = value

				# TODO: the code here uses n and node, why?

				elif n.name == "exit":
					llog("resolving exit")
					raise ExitCommand("", "exit command in node: [%s] '%s' from %s:%s" % (n.name, n.line, node.path(), node.linenr()))

				elif n.name == "skip":
					llog("resolving skip")
					raise SkipCommand("", "skip command in node: [%s] '%s' from %s:%s" % (n.name, n.line, node.path(), node.linenr()))

				elif n.name == "halt":
					llog("resolving continue")
					raise HaltCommand("", "halt command in node: [%s] '%s' from %s:%s" % (n.name, n.line, node.path(), node.linenr()))

				else:
					llog("unknown node: ", n, n.name, n.line)
					raise RuntimeError("unknown node: [%s] '%s' from %s:%s" % (n.name, n.line, node.path(), node.linenr()))

		except CommandException as e:
			result.append(e.result)
			result = "\n".join(result)
			# not sure if this is valid, modifying an exception on the fly to carry data, but it seems to work.
			e.result = result
			raise

		except RuntimeError as e:
			raise
		except EvaluationError as e:
			# See notes under "Exception chaining"
			raise EvaluationError(e, n), None, sys.exc_info()[2]
		except Exception as e:
			# See notes under "Exception chaining"
			raise EvaluationError(e, n), None, sys.exc_info()[2]

		llog("done")
		result = "\n".join(result)

		callstack.pop()
		return result


	def evaluatetokens(self, tokens, returnall = False):
		#result = self.pretzyl.evaltokens(tokens, count = None) # always return all results
		result = self.evaluator.evaltokens(tokens, count = None) # always return all results
		if returnall:
			# return all results.
			return result
		else:
			# we are requesting a single result. Make sure there is one and only one
			assert(len(result) == 1)
			return result[0]


class Context:
	"""act as dict-like interface to the stack of self.vars frames
	"""

	def __init__(self, initialenv):
		self.vars = [nsdict.NSDict(initialenv)]

	def push(self, vars = {}):
		"""Adds a new NSDict to the top of the self.vars stack.
		"""
		env = nsdict.NSDict()
		if vars is not None:
			env.update(vars)
		self.vars.append(env)
		return self

	def pop(self, result):
		"""Removes the top NSDict from the stack.
		Any 'output' entries are merged with the new stack top.
		"""
		assert(len(self.vars) > 1)
		vars = self.vars.pop()
		if "output" in vars:
			if "output" not in self.vars[-1]:
				self.vars[-1]["output"] = nsdict.NSDict()
			self.vars[-1]["output"].update(vars["output"])
		self['__output__'] = result
		return vars

	def __setitem__(self, name, value):
		# set always happens in the top frame
		self.vars[-1][name] = value

	def __getitem__(self, name):
		# try to find the name in the root stores of each frame
		for i in range(len(self.vars)-1, -1, -1):
			if name in self.vars[i]._store:
				return self.vars[i]._store[name]
		# if this doesn't work, do a deeper search on every frame
		for i in range(len(self.vars)-1, -1, -1):
			try:
				return self.vars[i][name]
			except KeyError as e:
				pass
		# if not found in the stack, raise a KeyError
		raise KeyError

	def __delitem__(self, name):
		# tries to remove the item in the current frame.
		# If not present (even if it exists in a previous frame), it is an error 
		self.vars[-1].__delitem__(name)

	def __getattr__(self, name):
		"""Convenience function to access data
		"""
		if name in self:
			return self[name]
		raise AttributeError("Environment has no attribute '%s'" % name)

	def update(self, vars, path = ''):
		return self.vars[-1][path].update(vars)

	def __len__(self):
		# returns the __len__ of the top of the stack
		# TODO: Should return the __len__ of the merged stacks.
		return len(self.vars[-1])

	def __iter__(self):
		# iterates over the current frame's vars
		# TODO: should iterate over the merged stack's vars
		return self.vars[-1].__iter__()

	def keys(self):
		# returns the current frame's keys
		# TODO: should return the merged stack's keys
		return self.vars[-1].keys()

	def dict(self):
		# returns the current frame's dict
		# TODO: should return the merged stack's dict
		return self.vars[-1].dict()

	def iteritems(self):
		return self.vars[-1].iteritems()

	def __contains__(self, name):
		for i in range(len(self.vars)-1, -1, -1):
			if name in self.vars[i]._store:
				return True
		# do a full name search
		for i in range(len(self.vars)-1, -1, -1):
			if name in self.vars[i]:
				return True
		return False


#######################################################################
#
# Exceptions
#

class BaseException(Exception):
	"""Base exception class for this module

	This Base class supports Exception chaining
	So in python 2.7, we do not have native exception chaining. However, to get the same effect, when re-raising an 
	exception, we can do https://stackoverflow.com/questions/1350671/inner-exception-with-traceback-in-python/1350981#1350981
	which basically comes down to
	> ...pass the traceback as the third argument to raise.
	> 
	> 	import sys
	> 	class MyException(Exception): pass
	> 	
	> 	try:
	> 	    raise TypeError("test")
	> 	except TypeError, e:
	> 	    raise MyException(), None, sys.exc_info()[2]
	This makes the entire exception chain available in the traceback, which greatly
	enhances debugging.
	"""
	def __init__(self, message):
		Exception.__init__(self, message)

class SyntaxError(BaseException):
	"""This is the main exception that is raised when errors occur in the Parser.
	"""
	def __init__(self, message):
		BaseException.__init__(self, message)

class RuntimeError(BaseException):
	"""This is the main exception that is raised when errors occur in the Renderer.
	"""
	def __init__(self, message):
		BaseException.__init__(self, message)

# re-use RuntimeError?
class EvaluationError(RuntimeError):
	"""Expression evaluation error

	This is a general chainable exception, and expects itself to be raised from another (source) exception.
	It therefore requires the triggering exception to be passed as a constructor argument, and
	will chain its message with that of the triggering exception.
	"""
	def __init__(self, exception, node):
		message = ""
		if not isinstance(exception, EvaluationError):
			message = exception.__class__.__name__ + " "
		message += exception.message + "\nnode [%s]: '%s' from %s:%i" % (node.name, node.line, node.path(), node.linenr())
		RuntimeError.__init__(self, message)

### Flow control exceptions
# These are raised during rendernode_'s execution when the parser sees one of %exit, %skip or %halt.
# They allow the template execution to break out of loops (%exit), continue to the next iteration of a loop (%skip),
# or completely terminate the execution %halt.
# In all cases, the already-generated output is preserved as much as possible.
#
# They do not inherit from Exception, so that we can cleanly catch these as a separate taxonomy.

class CommandException():
	"""Base command exception class

	This stores the accumulated results of the template execution at the point where it was raised,
	along with a message where it was generated in the source
	"""
	def __init__(self, result, message):
		self.result = result
		self.message = message

class ExitCommand(CommandException):
	"""%exit command exception
	This breaks out of a loop. Execution continues after the loop.
	In any other case (where there is no wrapping loop), template evaluation ends.
	"""
	def __init__(self, result, message):
		CommandException.__init__(self, result, message)

class SkipCommand(CommandException):
	"""%skip command exception
	This skips the current iteration of a loop and continues with the next iteration.
	In any other case (where there is no wrapping loop), template evaluation ends.
	"""
	def __init__(self, result, message):
		CommandException.__init__(self, result, message)

class HaltCommand(CommandException):
	"""%halt command exception
	This immediately terminates the evaluation of the template.
	"""
	def __init__(self, result, message):
		CommandException.__init__(self, result, message)



#######################################################################
#
# Command line usage
#

def parseargs(argv):
	"""Parses command line arguments

	All option arguments (starting with a dash '-') are interpreted as environment variables
	to be fed to the renderer. The leading dash is stripped, and the environment variable
	is set to the value following the equal sign '='.

	If no equal sign is present, the varaiable is set to 'True'.
	
	Any bare arguments are interpreted as filenames, and added to a list.
	
	Example:

		The arguments
			['-name=Jack', 'test.tpl']

		will set the environment to 
			{'name': 'Jack'}

		and return the list of files as
			['test.tpl']
	"""

	filenames = []
	env = {}
	for arg in argv[1:]:
		# bare arguments are filenames
		if arg.startswith("-"):
			optionarg = arg[1:]
			# option arguments are variables
			keyvalue = optionarg.split("=", 1)
			if len(keyvalue) == 1:
				env[optionarg] = True
			else:
				key, value = keyvalue
				env[key] = value
		else:
			filenames.append(arg)
	return filenames, env

def main(argv):
	"""Runs solon on a given environment and template file(s)

	The environment and filenames are extracted from the argument list.
	If there are no provided filenames, the template data is read from stdin.

	Each template is read and parsed in turn, and once all templates have been
	read they are rendered in turn.
	"""

	# grab the filenames and environment from the arguments
	filenames, env = parseargs(argv)

	# create a solon instance and feed it the environment
	s = Solon(env)

	# open all files for reading
	if len(filenames) == 0:
		# if no filenames were provided, read from stdin
		files = [("<stdin>", sys.stdin)]
	else:
		files = [(filename, open(filename, "r")) for filename in filenames]

	# parse each template in turn
	for filename, file in files:
		s.addtemplate(filename, file.read())

	# render each template in turn
	for filename, file in files:
		print s.rendertemplate(filename)

if __name__ == "__main__":
	# by default, run the main function on the commandline arguments
	main(sys.argv)

