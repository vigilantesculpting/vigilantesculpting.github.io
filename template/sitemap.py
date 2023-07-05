#!/usr/bin/env python3 

import os

# ---------------------------------------------------------------------
#  Create the sitemap
# ---------------------------------------------------------------------

def create(config, content):
	filepath = os.path.join(config.outputdir, config.tgtsubdir, "sitemap.txt")
	with open(filepath, "w") as f:
		# %for filepath: output None paths unpack sortpaths
		for filepath in []: #????
			f.write(f"{os.path.join(config.site_url, config.tgtsubdir, filepath)}\n")

