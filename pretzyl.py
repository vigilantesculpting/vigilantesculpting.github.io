#!/usr/bin/env python

"""A simple Forth-like stack based interpreter
"""

import tokenyze
import sys
import re
import os

#For internal debug use
LOG = False

def log(*args, **kwargs):
	"""For internal debug use
	"""
	if LOG:
		for arg in args:
			sys.stderr.write(str(arg))
		sys.stderr.write("\n")

def setlog(level):
	if level > 0:
		global LOG
		LOG = True
	tokenyze.setlog(level - 1)
	

#######################################################################
# Utilities


class Reference:
	"""Defines a Reference token

	Tokens can be Literals or References.
	References are names, that refer to values in an Environment.
	We encapsulate them in this class before pushing the raw names (strings) onto the stack, so that
	we can distinguish them from Literals later on.

	Literals are used as-is (ie. strings are strings, booleans are booleans, and numbers are numbers).
	"""

	def __init__(self, name):
		self.name = name

	def __repr__(self):
		return "Reference(%s)" % str(self.name)

	def __eq__(self, other):
		if isinstance(other, Reference):
			return self.name == other.name
		return False

	def __ne__(self, other):
		return not self.__eq__(other)

"""Some definitions used by the code
"""
QUOTES = "'", '"'
BOOLEANS = {"True": True, "False": False}
PUSHTOKEN = "("
POPTOKEN = ")"

def convert(token):
	"""This function takes a string token and converts it into a literal or reference.

	Literals are their own values. Pretzyl uses bare None, True / False, strings and numbers to represent these values.

	Tokens that cannot be converted as one of these, is encapsulated in a Reference instance,
	so that the rest of Pretzyl will know that these should refer to named values in the environment.
	"""
	if token == "None":
		return None
	if token in BOOLEANS:
		return BOOLEANS[token]
	try:
		if re.match(r"^-?0\d+$", token):
			number = int(token[1:], 8) # octal
		elif re.match(r"^-?0[xX][\da-fA-F]+$", token):
			number = int(token[2:], 16) # hex
		elif re.match(r"^-?\d+$", token):
			number = int(token) # base-10
		else:
			number = float(token)
		return number
	except ValueError:
		pass
	if len(token) > 1:
		quotes = token[0], token[-1]
		if quotes[0] == quotes[1] and quotes[0] in QUOTES:
			# must be a string
			return token[1:-1]
	# must be a reference
	return Reference(token)

def tokenize(line, macros, specialchars = ""):
	"""This method attempts to tokenize and translate an input line of program code.

	The macros is a dictionary of translations. It is applied after the initial
	tokenization to expand any macros in the line.
	"""
	log("tokenize line [%s] with specialchars [%s]" % (line, specialchars))
	tokenlist = []
	for token in tokenyze.gettokens(line, specialchars):
		if token in macros:
			# if the token is a macro, tokenize its macro expansion
			tokenlist.extend([token for token in tokenyze.gettokens(macros[token], specialchars)])
		else:
			# convert the non-macro token
			tokenlist.append(token)
	return tokenlist


#######################################################################
# Default operators

import functools
import math

class Operator:
	"""User-derived classes that want to implement operators should derive from this base class.

	Operator classes should implement
		def __call__(self, P)
	which takes a Pretzyl parser as argument when called during program execution.
	An operator class should be registered in the environment passed to the parser, in order to be available
	when a program invokes it using its reference name.
	"""
	def __init__(self):
		self.pretzyloperator = True
		pass

def MakeOperator(function, argc, argout = True, argextend = False, lookup = True, passenv = None):
	"""This is the main operator factory function

	It takes a number of parameters:
	- function: the function to map to the pretzyl stack,
	- argc: the number of items on the stack that are required to be able to feed the function,
	- argout: whether the return value from the function should be pushed onto the stack,
	- argextend: whether the return value from the function should extend the stack (rather than append to it),
	- lookup: whether the items that are popped from the stack should be looked up in the environment before
		being fed to the function, and
	- passend: whether the function expects the pretzyl instance to be passed as a first argument.

	The defaults are good for simple function arguments.
	For example
		MakeOperator(operator.add, 2)
	will create a pretzyl operator that takes two values (looked up in the environment), adds them using
	operator.add, and pushes the result to the stack.

	More complicated functions use parameters that are not default.
	For example, the 'exists' operator needs to know about the pretzyl environment, and its argument
	should not be looked up since it may not exist:
		MakeOperator(lambda P,a: P.validref(a), argc=1, lookup=False)

	Another more complicated example is a short-circuit 'and' operator.
	It needs to lookup the first parameter, but only needs to look up the second parameter if
	the first evaluates to true. If not, it can safely skip the second parameter and return false:
		MakeOperator(lambda P,a,b: P.lookup(b) if P.lookup(a) else False, argc=2, lookup=False)

	If the argc argument is None, the entire stack is popped and passed to the function.
	This is used by the 'enpack' operator, which pops the entire stack and returns it as a single list,
		MakeOperator(lambda a: a, argc=None)

	The 'unpack' operator, on the other hand, takes a single argument (a list), and uses the argextend=True
	spec to extend the stack using the items in the list:
		MakeOperator(lambda a: list(a), argc=1, argextend=True)

	So for example, the repeat operator 
	"""
	if passenv is None:
		# by default, if lookup is False, then passenv should be True and vice versa
		passenv = not lookup
	@functools.wraps(function)
	def wrapper(P):
		log("makeOperator: popping %s args from stack depth %i" % (argc, P.depth()))
		argv = P.pop(argc, lookup)
		if passenv:
			if argc is None:
				out = function(P, argv)
			else:
				out = function(P, *argv)
		else:
			if argc is None:
				out = function(argv)
			else:
				out = function(*argv)
		if argout:
			if argextend:
				P.extend(out)
			else:
				P.push(out)
	wrapper.pretzyloperator = True
	return wrapper

# A couple of utility functions, where the operator definitions require a couple of lines
# and lambdas or operator.* would not suffice

def makeop(P, a):
	"""Creates a reference out of the argument, then resolves it in the environment and
	attempts to apply it to the stack.
	This is used to create and run functions on the fly from names, eg.
		4 5 'sum'
		> 9
	"""
	ref = P.lookup(Reference(a))
	ref(P)

def repeat(P, a):
	"""Applies a named operator on the stack, until the stack is either too small or the iteration
	limit has been exceeded.
	This effectively reduces the stack, in the case where the operator produces less output than it takes in.
	For example,
		1 2 3 4 5 6 7 8 9 10 'add' repeat
		> 55
	"""
	ref = P.lookup(Reference(a))
	log("repeating operator %s:" % (a))
	for i in range(P.INFLIMIT):
		try:
			ref(P)
		except StackUnderflow as e:
			log("swallowed StackUnderflow exception from operator %s on iteration %i" % (a, i))
			return
	else:
		raise IterationOverflow("iteration limit exceeded in operator %s on iteration %i" % (a, i))

def and_(P, a, b):
	"""Short-circuit 'and' operator.
	The second argument is not looked up if the first argument evaluates to False
	"""
	return P.lookup(b) if P.lookup(a) else False

def or_(P, a, b):
	"""Short-circuit 'or' operator.
	The second argument is not looked up if the first argument evaluates to True
	"""
	return P.lookup(b) if not P.lookup(a) else True

def truncate(text):
	"""Truncates a piece of html text at the required number of words
	"""
	words = 25
	return ' '.join(re.sub('(?s)<.*?>', ' ', text).split()[:words])

def _sum(list):
	"""Adds the items of a list together.
	If the list is empty, an empty list is returned.
	"""
	if len(list) > 0:
		if isinstance(list[0], str):
			return ''.join(list)
		return sum(list[1:], list[0])
	else:
		return []

def strsum(list):
	"""Converts each element in a list to a string, and returns all the concatenated strings
	"""
	return ''.join((str(s) for s in list))

def slice_(a, start, end):
	"""Returns a slice of a parameter, a[start:end]
	If start is None, it returns a[:end]
	If end is None, it returns a[start:]
	"""
	if start is None:
		return a[:end]
	if end is None:
		return a[start:]
	return a[start:end]

def endslice(a, start):
	"""Returns the start slice, up to start
	"""
	return a[start:]

def startslice(a, end):
	"""Returns the end slice, from end
	"""
	return a[:end]

def splitat(a, index):
	"""Splits a list into two pieces, at the index provided
	"""
	return a[:index], a[index:]

def groupby(a, groupsize):
	"""Breaks a list of items into groups of groupsize.
	The last group will contain the remaainder.
	For example "(1 2 3 4 5 6 7 8) 3 groupby"
	will return [[1, 2, 3], [4, 5, 6], [7, 8]]
	Note: this returns a generator, so using something like "length" on the result of this operator
	will fail hard.
	"""
	return (a[i:i + groupsize] for i in range(0, len(a), groupsize))

def sortpaths(pathlist):
	return sorted(pathlist, key=lambda path: os.path.split(path))

def methodcaller(name):
	"""Invokes the named method on an object, using the arguments provided
	"""
	def methodcaller_(obj, *args, **kwargs):
		op = operator.methodcaller(name, *args, **kwargs)
		return op(obj)
	return methodcaller_


# A handy dictionary of the default operators.
# Note: Some of the operators will return generators, which may result in a 
# 		"TypeError: object of type 'generator' has no len()"
# exception when trying to apply eg. the "length" operator on the result.
# Examples include 'enumerate', 'range', 'iteritmes' and 'groupby'

import operator

DefaultOperators = {
	'exists'		: MakeOperator(lambda P,a: P.validref(a), argc=1, lookup=False),
	'not' 			: MakeOperator(operator.not_, argc=1),
	'isnone'		: MakeOperator(lambda a: a is None, argc=1),
	'makeref' 		: MakeOperator(Reference, argc=1),
	'makeop' 		: MakeOperator(makeop, argc=1, argout=False, passenv=True),
	'length' 		: MakeOperator(len, argc=1),
	'dup'			: MakeOperator(lambda P:P.peek(), argc=0, lookup=False),
	'unpack' 		: MakeOperator(lambda a: list(a), argc=1, argextend=True),
	'enpack' 		: MakeOperator(lambda a: a, argc=None),
	'int' 			: MakeOperator(int, argc=1),
	'str' 			: MakeOperator(str, argc=1),

	'enumerate' 	: MakeOperator(enumerate, argc=1),
	'range' 		: MakeOperator(range, argc=1),
	'iteritems' 	: MakeOperator(methodcaller('iteritems'), argc=1),

	'ceil' 			: MakeOperator(math.ceil, argc=1),
	'floor'			: MakeOperator(math.floor, argc=1),

	'gt'			: MakeOperator(operator.gt, argc=2),
	'lt'			: MakeOperator(operator.lt, argc=2),
	'eq' 			: MakeOperator(operator.eq, argc=2),
	'ge'			: MakeOperator(operator.ge, argc=2),
	'and' 			: MakeOperator(and_, argc=2, lookup=False),
	'or' 			: MakeOperator(or_, argc=2, lookup=False),
	'mul' 			: MakeOperator(operator.mul, argc=2),
	'add' 			: MakeOperator(operator.add, argc=2),
	'sub' 			: MakeOperator(operator.sub, argc=2),
	'intdiv' 		: MakeOperator(operator.div, argc=2),
	'floatdiv'		: MakeOperator(operator.truediv, argc=2),
	'pow' 			: MakeOperator(operator.pow, argc=2),

	'at' 			: MakeOperator(operator.getitem, argc=2),
	'contains' 		: MakeOperator(operator.contains, argc=2),

	'startswith' 	: MakeOperator(methodcaller('startswith'), argc=2),
	'endswith' 		: MakeOperator(methodcaller('endswith'), argc=2),
	'paths' 		: MakeOperator(methodcaller('paths'), argc=2),
	'strftime'  	: MakeOperator(methodcaller('strftime'), argc=2),

	'pathjoin' 		: MakeOperator(os.path.join, argc=2),
	'groupby' 		: MakeOperator(groupby, argc=2),
	'startslice' 	: MakeOperator(startslice, argc=2),
	'endslice' 		: MakeOperator(endslice, argc=2),
	'splitat' 		: MakeOperator(splitat, argc=2, argextend=True),
	'swap'			: MakeOperator(lambda a,b: (b,a), argc=2, argextend=True),

	'choose' 		: MakeOperator(lambda first,second,predicate: first if predicate else second, argc=3),
	'slice' 		: MakeOperator(slice_, argc=3),

	'pathsum' 		: MakeOperator(lambda a: os.path.join(*a), argc=None),
	'sum' 			: MakeOperator(_sum, argc=None),
	'strsum' 		: MakeOperator(strsum, argc=None),
	'sortpaths' 	: MakeOperator(sortpaths, argc=None),

	'truncate'		: MakeOperator(truncate, argc=1),

	'repeat' 		: MakeOperator(repeat, argc=1, argout=False, passenv=True),
}

# A handy dictionary of macro symbols.
# Macros are expanded only once, so we cannot use macros inside macros (ie. no nesting)
# This is only for convenience / basic syntactic sugar.

MacroSymbols = {
	'>': 		'gt',
	'<':		'lt',
	'==':		'eq',
	'>=':		'ge',
	'!':		'not',
	'!none':	'isnone not',
	'&': 		'and',
	'|': 		'or',
	'~': 		'makeref',
	'*': 		'mul',
	'+': 		'add',
	'-': 		'sub',
	'/': 		'floatdiv', 		# "14 5 /"  -> 14.0 / 5.0 == 2.8
	'//': 		'intdiv', 			# "14 5 //" -> 14   / 5   == 2
	'^': 		'ceil',
	'/^': 		'floatdiv ceil', 	# "14 5 /^"  -> 14.0 / 5.0 ceil == 3.0
	'_': 		'floor',
	'<>': 		'at',
	'||': 		'length',
	'[]': 		'slice',
	':]': 		'startslice',
	'[:': 		'endslice',
	'{}': 		'groupby',
	'?': 		'choose',
	'?]': 		'startswith',
	'[?': 		'endswith',
	'@': 		'iteritems',
	'prod': 	'"mul" repeat',
	'//+': 		'pathsum',
	'/+': 		'pathjoin',
	'**': 		'pow',
	'*2': 		'2 pow',
}

###############################################################################
# The Pretzyl class


class Pretzyl:
	"""This is the core interpreter of Pretzyl

	It defines both the external API for a user to process a program with,a
	as well as the operator API with which operators (both default and custom)
	can interact with the stack.

	It processes a text program into tokens, evaluates each token in turn,
	and arranges the output on a heap of stacks. It also holds the environment,
	with which operators can interact using the stack.
	"""

	STACKLIMIT = sys.maxsize
	STACKDEPTH = 100
	INFLIMIT = 2**10 # set to float('Inf') for no limit

	def __init__(self, environment = {}, operators = DefaultOperators, operatorpath = None, macros = MacroSymbols):
		self.env = environment
		self.operatorpath = operatorpath
		self.macros = macros if macros is not None else {}
		self.operatorpath = operatorpath
		if operatorpath is None:
			self.env.update(operators)
		else:
			# this assumes that self.env has an update that takes a path
			self.env.update(operators, self.operatorpath)

	def getopenv(self):
		"""Returns the part of the environment where operators can be found
		"""
		if self.operatorpath is None:
			return self.env
		else:
			return self.env[self.operatorpath]

	def validref(self, token):
		"""Checks whether a token is a valid reference in the environment
		"""
		return isinstance(token, Reference) and token.name in self.env

	def lookup(self, token):
		"""Resolves the value of a token.
		Reference tokens refer to objects in the environment. If a reference refers
		to a non-existent object, an InvalidReference exception is raised.
		Literal tokens are their own value.
		"""
		if isinstance(token, Reference):
			try:
				return self.env[token.name]
			except KeyError as e:
				raise InvalidReference("token with name [%s] not found" % token.name)
		return token

	def checkstack(self, minsize):
		"""Checks whether the stack has (at least) the required minsize length
		"""
		if self.depth() < minsize:
			raise StackUnderflow("stack depth %i is shallower than required %i" % (self.depth(), minsize))

	def peek(self, count = 1, lookup = True):
		"""Returns the specified number of tokens from the top of the stack, without popping them.
		If lookup is specified, reference tokens are resolved in the environment and their objects returned.
		"""
		self.checkstack(count)
		items = self.stacks[-1][-count:]
		if lookup:
			items = [self.lookup(item) for item in items]
		return items[0] if len(items) == 1 else items if len(items) > 1 else None

	def pop(self, count = 1, lookup = True):
		"""Returns the top count tokens in the stack
		The tokens are removed from the stack.
		They are returned in FIFO order, and if lookup is True,
		their values in the environment are looked up. 
		"""
		if count is None:
			# return eveything:
			self.stacks[-1], items = [], self.stacks[-1]
		else:
			self.checkstack(count)
			if count > 0:
				# chop the last count items off the stack
				self.stacks[-1], items = self.stacks[-1][:-count], self.stacks[-1][-count:]
				assert(len(items) == count)
			else:
				# nothing to do, return an empty list (count is 0)
				return []
			assert(len(items) == count)
		# do lookup, if required
		if lookup:
			items = [self.lookup(item) for item in items]
		return items

	def push(self, value):
		"""Pushes a token onto the topmost stack
		"""
		if self.depth() + 1 > self.STACKLIMIT:
			raise StackOverflow("stack overflow, stack depth %i exceeds STACKLIMIT %i" % (self.depth(), self.STACKLIMIT))
		self.stacks[-1].append(value)

	def extend(self, list):
		"""Appends a list of tokens onto the topmost stack
		"""
		if self.depth() + len(list) > self.STACKLIMIT:
			raise StackOverflow("stack overflow, stack depth %i exceeds STACKLIMIT %i" % (self.depth(), self.STACKLIMIT))
		self.stacks[-1].extend(list)

	def depth(self):
		"""Retuens the depth of the topmost stack
		"""
		return len(self.stacks[-1])

	def pushstack(self):
		"""Adds a stack to the heap of stacks
		The stack becomes the new active top stack.
		This is done when an opening bracket token is found.
		"""
		if len(self.stacks) + 1 > self.STACKDEPTH:
			raise RecursionOverflow("recursion overflow, stacks size %i exceeds STACKDEPTH %i" % (len(self.stacks), self.STACKDEPTH))
		self.stacks.append([])

	def popstack(self):
		"""Pops the top stack from the heap of stacks
		The contents of the stack is added to the new top stack.
		This is done when an closing bracket token is found.
		"""
		if len(self.stacks) == 1:
			raise NestingException("cannot pop last stack")
		laststack = self.stacks.pop()
		if len(laststack) == 1:
			self.push(laststack[0])
		elif len(laststack) > 1:
			self.push(laststack)
		else:
			pass

	def getoperator(self, token):
		"""This method attempts to get an operator (possibly with modifier) from a token
		If succesful, the operator is returned.
		Otherwise, the method returns None
		"""
		log("makeoperator[%s]:" % token)
		if not isinstance(token, Reference):
			# simply return false, this is not a reference
			log("-> not a reference")
			return None
		openv = self.getopenv()
		try:
			obj = openv[token.name]
			if not obj.__dict__['pretzyloperator']:
				log("-> found object is not a proper operator")
				return None
		except KeyError as e:
			log("-> obj not found in openv")
			return None
		except AttributeError as e:
			log("-> error accessing attributes, discarding operator")
			return None
		operator = obj
		return operator

	def runoperator(self, operator):
		log("running operator [%s], last operator is [%s]" % (operator, self.lastop))
		operator(self)
		self.lastop = operator

	def tokenize(self, line, specialchars = ""):
		tokens = [convert(token) for token in tokenize(line, self.macros, specialchars = specialchars)]
		return tokens

	def evaltokens(self, tokens, count = 1, lookup = True):
		"""This method evaluates a complete program.
		It returns the count number of items from the bottom level stack, and looks
		up their values in the environment if requested.
		"""
		log("evaltokens: ", tokens)
		# each evaluation starts off with a new stack
		self.stacks = [[]]
		self.lastop = None
		log("tokens are ", tokens)
		#tokens.reverse()
		# evaluate one token at a time.
		#while len(tokens) > 0:
		for token in tokens:
			#token = tokens.pop()
			log("looking at token [%s], stack depth: %i" % (token, self.depth()))
			if isinstance(token, Reference):
				if token.name == PUSHTOKEN:
					log("-> token is PUSHTOKEN")
					# push a new input stack on top of the old stack
					self.pushstack()
					continue
				elif token.name == POPTOKEN:
					log("-> token is POPTOKEN")
					# pop the current stack, add its value to the next stack
					self.popstack()
					continue
				else:
					operator = self.getoperator(token)
					if operator is not None:
						self.runoperator(operator)
						continue
			# otherwise push it onto the stack
			log("-> token [%s] is a literal, adding to stack" % token)
			self.push(token)
		# we need to make sure our stackdepth is 1
		if len(self.stacks) != 1:
			# probably a syntax error: no matching closing bracket.
			raise NestingException("syntax error, missing closing bracket(s) for [%s]" % tokens)
		return self.pop(count, lookup)

	def eval(self, line, count = 1, lookup = True):
		"""This method evaluates a complete program.
		It returns the count number of items from the bottom level stack, and looks
		up their values in the environment if requested.
		"""
		log("eval: [%s]" % line)
		if not isinstance(line, str):
			# we expect a string here
			raise RuntimeError("expected a string, found type %s instead: " % (type(line)), line)
		# do macro symbol translation and tokenize the line:
		tokens = self.tokenize(line)
		return self.evaltokens(tokens, count, lookup)


#######################################################################
### Exceptions

class BaseException(Exception):
	"""Base exception class for this module
	"""
	def __init__(self, message):
		Exception.__init__(self, message)

class RecursionOverflow(BaseException):
	"""Recursion overflow

	This exception is raised when the stack depth exceeds the STACKDEPTH limit, ie. there 
	are too may heirarchical open brackets in the program
	"""
	def __init__(self, message):
		BaseException.__init__(self, message)

class NestingException(BaseException):
	"""Nesting exception

	This is raised when there are mismatched brackets in the program. Either one too many
	closing brackets, or too few closing brackets.
	In either case, the number and nesting of brackets do not match.
	This is a syntax error in the program.
	"""
	def __init__(self, message):
		BaseException.__init__(self, message)

class StackUnderflow(BaseException):
	"""Stack underflow

	Raised by the interpreter when an operation attempts to pop more values
	off the stack than are currently available.
	"""
	def __init__(self, message):
		BaseException.__init__(self, message)

class StackOverflow(BaseException):
	"""Stack overflow

	Raised by the interpreter when an operation attempts to push more values
	onto the stack than are currently allowed.
	"""
	def __init__(self, message):
		BaseException.__init__(self, message)

class IterationOverflow(BaseException):
	"""Iteration overflow

	Raised by the interpreter when a modified inf repeat operation does not terminate
	before the expected number of iterations.
	"""
	def __init__(self, message):
		BaseException.__init__(self, message)

class InvalidReference(BaseException):
	"""Invalid reference token lookup
	"""
	def __init__(self, message):
		BaseException.__init__(self, message)

class MalformedOperator(BaseException):
	"""Operator syntax error

	This is an internal exception that is used during operator parsing, to indicate
	that the operator (specifically, its modifier) is malformed, and that the 
	operator should be treated as a regular reference instead.
	"""
	def __init__(self, message):
		BaseException.__init__(self, message)

class ExecutionException(BaseException):
	def __init__(self, exception, message):
		message = repr(exception) + message
		BaseException.__init__(self, message)

