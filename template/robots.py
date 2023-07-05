#!/usr/bin/env python3

import os

# ---------------------------------------------------------------------
#  Create the robots.txt file
# ---------------------------------------------------------------------

def create(config, content):
	filepath = os.path.join(config.outputdir, config.tgtsubdir, "robots.txt")
	with open(filepath, "w") as f:
		f.write(f"""\
User-agent: *
Disallow:

SITEMAP: {os.path.join(config.site_url, config.tgtsubdir, 'sitemap.txt')}
""")