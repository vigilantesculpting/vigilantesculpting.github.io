#!/usr/bin/env python

"""NSDict is a namespaced dictionary-like container class for Python

	This class stores data in a hierarchical fashion, with namespaced strings as keys.

	Internally, an NSDict stores keys and values in a dictionary.
	Keys have to be strings, but values can be anything, including other NSDicts, hence the hierarchy.

	When an NSDict is queried with a namespaced string, the string is broken into its various branches,
	and each NSDict corresponding to a branch is queried until the final leaf NSDict, and its values
	are returned, which may be a single value, or again a whole NSDict.

	NSDicts can be updated, and only leaf values will be overwritten. Leaf NSDicts will be updated
	with the incoming data.

	NSDicts can be used to represent text data from a filesystem, for example, with paths represented
	by the namespace branches, and key/value pairs from the files themselves stored as the leaf
	key/values.

	Since values can be arrays, or anything else Python permits, data in the tree can be postprocessed
	and reassigned for iteration.

Example usage:

	# import the NSDict code

	>>> from nsdict import NSDict

	# pepare a dict with some initial data.
	# Note that the keys are all of the form "{string0}.{string1}..."
	# These form our namespaces, for example {string1} lives in the namespace of {string0}

	>>> d = { 
	...     "root.branch1.leaf1": "value1",
	...     "root.branch1.leaf2": "value2",
	...     "root.branch2.leaf3": "value3",
	... }

	# create an NSDict from the data
	>>> D = NSDict(d)

	# The string __repr__ method of an NSDict spits out the namespaced keys and values in the container:
	>>> D
	root.branch2.leaf3: value3
	root.branch1.leaf1: value1
	root.branch1.leaf2: value2

	# D is of type NSDict
	>>> type(D)
	<class 'nsdict.NSDict'>

	# D has the following key, in this case only one, the cleverly named "root" namespace
	>>> D.keys()
	['root']

	# Let's see what root has for keys():
	>>> D["root"].keys()
	['branch2', 'branch1']

	# ...and let's see what root.branch1 has for keys...
	>>> D["root.branch1"].keys()
	['leaf1', 'leaf2']

	# Since NSDict claims to be a dict-like container, let's iterate over the key/value pairs in the
	# root namespace:
	>>> for key, value in D["root"].iteritems():
	...     print "[%s] -> [%s]" % (key, value)
	... 
	[branch2] -> [leaf3: value3]
	[branch1] -> [leaf1: value1
	leaf2: value2]

	# So it looks like branch1 contains another NSDict...

	# NSDicts can return a dict of their contents. This will assemble the namespaced keys as single individual
	# keys in a dict, with their corresponding values:
	>>> for key in D.dict().keys():
	...     print "[%s] -> [%s]" % (key, D[key])
	... 
	[root.branch1.leaf2] -> [value2]
	[root.branch1.leaf1] -> [value1]
	[root.branch2.leaf3] -> [value3]

	# When we grab a subtree in a namespace:
	>>> E = D["root.branch1"]
	>>> E
	leaf1: value1
	leaf2: value2

	# we can see it is also an NSDict,
	>>> type(E)
	<class 'nsdict.NSDict'>

	# and it has the namespaced keys of that namespace, now as root keys, with their values
	>>> E.dict().keys()
	['leaf1', 'leaf2']

	So basically an NSDict is a hierarchical tree structure, with a namespaced string key system.

Why in the ever loving f...?

	Because I can.

	Also, it is useful for making environments for simple computer languages, such as pretzyl.

"""

import collections
import sys

# For internal debugging use
LOG = False

def log(*args, **kwargs):
	"""For internal debugging use
	"""
	if LOG:
		for arg in args:
			sys.stderr.write(str(arg))
		sys.stderr.write("\n")

def setlog(level):
	if level > 0:
		global LOG
		LOG = True

class NSDict(collections.MutableMapping):
	"""The NSDict container class

	Stores data in a recursive dictionary structure, where all keys
	are strings, and nested dictionaries can be accessed via namespaced
	strings.

	Namespaced strings are simply the individual strings concatenated with the DELIMITER.
	"""

	DELIMITER = "/"
	SEPERATOR = ":"

	def __init__(self, *args, **kwargs):
		"""Initialises an NSDict with values.
		args are expected to be dict-like, so dicitonaries and other NSDicts will be fine.
		Keyword args are treated as simple key/value pairs.
		"""
		self._store = {}
		log("initialising with ", *args, **kwargs)
		for arg in args:
			for key, value in arg.iteritems():
				log("adding ", key)#, " -> ", value)
				self.__setitem__(key, value)
		for key, value in kwargs:
			self.__setitem__(key, value)

	def __str__(self):
		"""The default string representation of an NSDict is simply the flattened NSDict
		"""
		return "\n".join(self._flatten())

	def _flatten(self):
		"""This method flattens the NSDict into a string object,
		formatted to represent the layout of the container and its namespaced data
		"""
		entries = []
		for key, value in self._store.iteritems():
			if isinstance(value, NSDict):
				for entry in value._flatten():
					entry = key + self.DELIMITER + entry
					entries.append(entry)
			else:
				strvalue = str(value)
				entries.append(key + self.SEPERATOR + " " + strvalue)
		return entries

	def dict(self):
		"""Returns the dict-representation of an NSDict
		This collects the namespaced key for each value, and returns the 
		namespaced-key/value pairs as a dict.
		"""
		d = {}
		for key, value in self._store.iteritems():
			if isinstance(value, NSDict):
				for k, v in value.dict().iteritems():
					entry = key + self.DELIMITER + k
					d[entry] = v
			else:
				# TODO: chop at the first newline, so we can keep our sanity
				d[key] = value
		return d

	def _splitname(self, name):
		"""Internal function: splits a namespaced name into its branches
		"""
		subnames = name.split(self.DELIMITER, 1)
		return subnames

	def __getitem__(self, name):
		"""MutableMapping interface: get item using namespace key
		Starting with the root store, look for each value that corresponds
		to one of the branchnames, and return the final value.
		Raises KeyError if the namespace could not be resolved.
		"""
		if len(name) == 0:
			return self
		subnames = self._splitname(name)
		try:
			if len(subnames) == 1:
				return self._store[name]
			else:
				rootname, rest = subnames
				return self._store[rootname][rest]
		except Exception as e:
			raise KeyError

	def __getattr__(self, name):
		"""Convenience function to access data
		This interprets the attribute name as a key in the root self._store.
		It allows funkiness like
		>>> r = NSDict({'hello' : 'world'})
		>>> r.hello
		'world'
		This access is read-only, no __setattr__ is defined, so using the above
		example
		>>> r.allo = 'monde'
		will result in an AttributeError
		"""
		if name in self._store:
			return self._store[name]
		raise AttributeError("NSDict has no attribute '%s'" % name)

	def __setitem__(self, name, value):
		subnames = self._splitname(name)
		if len(subnames) == 1:
			if name in self._store and isinstance(self._store[name], NSDict) and (isinstance(value, NSDict) or isinstance(value, dict)):
				# merging leafname with value (both NSDicts)
				for k in value.keys():
					self._store[name][k] = value[k]
			else:
				# overwriting name with value
				self._store[name] = value
		else:
			rootname, rest = subnames
			if rootname not in self._store or not isinstance(self._store[rootname], NSDict):
				# overwriting name with NSDict
				self._store[rootname] = NSDict()
			# overwriting name with value
			self._store[rootname][rest] = value

	def __delitem__(self, name):
		"""Find and remove the value at the given namespace name
		Raises KeyError if the branch does not exist.
		"""
		subnames = self._splitname(name)
		if len(subnames) == 1:
			del self._store[name]
		else:
			rootname, rest = subnames
			del self._store[rootname][rest]

	def __len__(self):
		"""Returns the number of root branches
		"""
		return len(self._store)

	def __iter__(self):
		"""Iterates over all the root branches
		"""
		return iter(self._store.keys())

	def keys(self):
		"""Returns all the root branch keys
		"""
		return self._store.keys()

	def paths(self, depth = None):
		"""Returns all the recursive keys
		"""
		newdepth = None
		if depth is not None:
			newdepth = depth - 1
		d = []
		if newdepth is None or newdepth > 0:
			for key in self._store.keys():
				value = self._store[key]
				if isinstance(value, NSDict):
					keys = value.paths(newdepth)
					d.extend([key + self.DELIMITER + k for k in keys])
				else:
					d.append(key)
		else:
			d.extend(self._store.keys())
		return d

	def __contains__(self, name):
		"""Checks to see if the namespaced name exists
		The implementation abuses __getitem__ and abuses
		the KeyError if any is generated.
		"""
		subnames = self._splitname(name)
		if len(subnames) == 1:
			if name in self._store:
				return True
		else:
			rootname, rest = subnames
			try:
				return rest in self._store[rootname]
			except KeyError as e:
				return False

	# TODO, might be useful...
	#def walk(self, depth, depthfirst):
	#	# creates a generator that will walk the structure of the tree,
	#	# visiting each namespace in turn and providing a list of
	#	# branches at that namespace.
	#	# If depth is specified, the iteration stops at that depth
	#	# If depthfirst is specified, the iteration starts at the leaves,
	#	# and works its way upward.


#######################################################################
# Some simple (but ugly) tests
# these need a good improvement, some corner cases, cleanup and some structure...

def test():
	try:
		import pdb
		import traceback

		global LOG
		LOG = True
		
		log("initialising d...")
		d = NSDict()

		log("updating d...")

		d["hello.world"] = "greetings!"
		log("d is:\n", d)
		log("d.dict() is\n", d.dict())

		d.update({'hello.jack': 'greetings!'})
		d.update({'hello.sammy': 'universe'})
		log("d is:\n", d)
		log("d.dict() is\n", d.dict())
		#return

		d.update({'hello.jack.dolt': 'blahblah'}) # should overwrite d._store["hello"]._store["jack"] with an NSDict 

		log("d is:\n", d)
		log("d.dict() is\n", d.dict())
		#return

		log("initialising s...")

		s = NSDict({'jack': 'universe', 'dolt': 'greetings!'})

		log("s is:\n", s)

		d.update(s)
		log("d is:\n", d)
		log("d.dict() is\n", d.dict())

		return
		log("assertions...")

		assert(d["hello.world"] ==
			'greetings!'
		)


		log("checking s...")

		pdb.set_trace()

		assert(d["hello"] ==
			s
		)


		b = NSDict(d)

		print "d.keys()                :", d.keys()
		print "d['hello'].keys()       :", d['hello'].keys()
		print "d['hello']              :", d['hello']
		print "d['hello.world']        :", d['hello.world']
		print "items in d['hello']:"
		for key, value in d['hello'].iteritems():
			print key, '->', value
		print "d['hello.jack.dolt'] :", d['hello.jack.dolt']
		print "d: ", d
		print "d.flatten(): "
		print "\n".join(d.flatten())
	except:
		traceback.print_exc()
		pdb.post_mortem()


if __name__ == "__main__":
	test()
