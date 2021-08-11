#!/usr/bin/env python

"""tokenyze is a Python tokenizer
It uses generators to do a look-ahead tokenizing of an input string.

Tokens are defined as names or strings, and can be nested using brackets.
Names are made up of sequential non-whitespace characters.
Brackets are special single letter tokens.
Strings are delimited by either single or double quotes.
Backslashes can escape these characters.

Example:

	The text

	    "fr33(the p1zza c@t)n0w_",

	will result in the following (generated) token list:

	    ['fr33', '(', 'the', 'p1zza', 'c@t', ')', 'n0w_']

Implementation:

	The code uses a generator (getchars) to deliver character from the text
	to the gettokens consumer. The consumer will pass on responsibility
	for parsing the text to either a whitespace consumer (eatwhitespace)
	or a token consumer, which will in turn defer to a name consumner
	(eatname) or string consumner (eatstring).

	The gettokens consumer itself is a generator, which will yield each 
	found token in turn until there are no more tokens left.

Usage:

	$ python
	>>> import tokenyze
	>>> for token in tokenyze.gettokens("fr33(the p1zza c@t)n0w_"):
	...     print token
	... 
	fr33
	(
	the
	p1zza
	c@t
	)
	n0w_
	>>> 


"""

LOG = False
import sys

def setlog(level):
	if level > 0:
		global LOG
		LOG = True

def log(*args, **kwargs):
	"""For internal debug use
	"""
	if LOG:
		for arg in args:
			sys.stderr.write(str(arg))
		sys.stderr.write("\n")

def getchars(text):
	"""character iterator

	This generator iterates over the characters in the text
	"""

	for nextchar in text:
		yield nextchar

def eatwhitespace(nextchar, TEXT):
	"""whitespace eater

	This eats whitespace, and returns the next non-whitespace character
	"""
	log("-eat whitespace")
	while True:
		if nextchar is not None:
			if nextchar == "\\":
				nextchar = nextchar + TEXT.next()
			if nextchar not in " \t\n":
				log("-found non-whitespace:", nextchar)
				return nextchar
		nextchar = TEXT.next()

def eatstring(nextchar, TEXT):
	"""string eater

	This eats a string, until the starting quote of the string is found.
	Strings are returned with their enclosing quotes!
	"""
	log("-eat string")
	# start the string with the new character, this will be a quote
	string = nextchar
	while True:
		try:
			nextchar = TEXT.next()
		except StopIteration as e:
			# if we run out of characters in the text, return the name
			log("-stop string: ", string, None)
			return string, None

		if nextchar == "\\":
			nextchar = nextchar + TEXT.next()
			string += nextchar[-1]
			continue

		string += nextchar[-1]
		if nextchar == string[0]:
			# if we see the same quote as the opening quote, the string
			# is complete.
			log("-return string: ", string, None)
			return string, None

def eatname(specialchars, nextchar, TEXT):
	"""name eater

	This eats a name, until either a non-name character
	is seen, or another token (brackets) starts.
	"""
	log("-eat name")
	if nextchar in "()" + specialchars:
		# hard return on bracket, and return the next character as an empty string.
		return nextchar, ''
	# start the new name with the new character
	name = nextchar[-1]
	while True:
		try:
			nextchar = TEXT.next()
		except StopIteration as e:
			# if we run out of characters in the text, return the name
			log("-stop name: ", name, None)
			return name, None

		log("-name char", nextchar)
		if nextchar == "\\":
			nextchar = nextchar + TEXT.next()

		if nextchar in " \t\n()'\"" + specialchars:
			log("-return name: ", name, nextchar)
			return name, nextchar

		name += nextchar[-1]

def eattoken(specialchars, nextchar, TEXT):
	"""token eater

	This decides whether the next token will be a string or a name, depending
	on the look-ahead character
	"""

	log("-eat token")
	if nextchar in ("'", '"'):
		return eatstring(nextchar, TEXT)
	else:
		return eatname(specialchars, nextchar, TEXT)

def gettokens(text, specialchars = ''):
	"""gettokens is a generator that splits a text into tokens
	"""

	log("-make D generator")
	# create a generator that will provide us with one character at a time
	TEXT = getchars(text)
	# grab the first character. This is our look-ahead
	nextchar = TEXT.next()
	while True:
		# eat all following white space. Return the first non-whitespace character
		nextchar = eatwhitespace(nextchar, TEXT)
		# feed the look-ahead character to the token eater
		token, nextchar = eattoken(specialchars, nextchar, TEXT)
		# we get the token and the next non-token character back
		log("-yield token", token)
		yield token


##### some unit tests #################################################

if __name__ == "__main__":
	LOG = True
	import sys
	import pdb
	import traceback

	def test(string, expected):
		log(string)
		# add ":" as a specialchar
		tokens = list(gettokens(string, ":"))
		log(tokens)
		assert(len(expected) == len(tokens))
		assert(all([a == b for (a, b) in zip(tokens, expected)]))

	try:
		# simple test
		test(
			"hello world!",
			['hello', 'world!']
		)

		# a bit more complex, we have brackets breaking up strings of text
		test(
			"fr33(the p1zza c@t)n0w_",
			['fr33', '(', 'the', 'p1zza', 'c@t', ')', 'n0w_']
		)

		# string should be able to contain extra specialchars
		test(
			"fr33(the 'p1:zza' c@t)n0w_",
			['fr33', '(', 'the', "'p1:zza'", 'c@t', ')', 'n0w_']
		)

		# check for extra specialchars
		test(
			"fr3:3(the p1zza c@t)n0w_",
			['fr3', ':', '3', '(', 'the', 'p1zza', 'c@t', ')', 'n0w_']
		)

		# test escaped characters
		test(
			"eat(the\tchopper\n\\)boppers\ttoday",
			['eat', '(', 'the', 'chopper', ')boppers', 'today']
		)

		# random nonsense
		test(
			"hello $ %_!\nwo('orld (r)\" '\"mole\")bl\tah(foo)(bar)\\(wack",
			['hello', '$', '%_!', 'wo', '(', '\'orld (r)" \'', '"mole"', ')', 'bl', 'ah', '(', 'foo', ')', '(', 'bar', ')', '(wack']
		)

		# more random nonsense
		test(
			"hdcs43(operator*'230 lkcank 23245'\"dckjnkasd(sdclk)\"csdkk(kjk kjnkjn)(caskdjkj)( sdcklkldc)\")\"",
			['hdcs43', '(', 'operator*', "'230 lkcank 23245'", '"dckjnkasd(sdclk)"', 'csdkk', '(', 'kjk', 'kjnkjn', ')', '(', 'caskdjkj', ')', '(', 'sdcklkldc', ')', '")"']
		)

	except:
		traceback.print_exc()
		pdb.post_mortem()
