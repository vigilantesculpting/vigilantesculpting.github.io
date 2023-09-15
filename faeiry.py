#!/usr/bin/env python3

import sys
import glob
import getopt
import os
import json
import webbrowser
from PIL import Image

from imgurpython import ImgurClient

# faeirysecrets should define two variables: client_id and client_secret
from faeirysecrets import *
credentialsfilepath = '~/.faeiry.json'

# TODO:
# - Convert this to a module, so that we can call it from another python script with a batch of images to upload,
# 	and return a batch of urls on success
# 
# x Add the credentials file path
# x Add images to an existing album
# x Query mode: list images in an album
# x Specify the title of an album
# x spit out the urls of the images
# - strict: sanity check all images - they must be a specified maximum WIDTH, HEIGHT and SIZE
# - retry: if an image upload fails, wait a specified number of seconds, then retry

def authenticate(cfilepath = None):
	if cfilepath is None:
		cfilepath = credentialsfilepath
	try:
		credentialfile = open(cfilepath, 'r')

		credentials = json.load(credentialfile)

		# Note since access tokens expire after an hour, only the refresh token is required (library handles autorefresh)
		client = ImgurClient(client_id, client_secret, credentials['access_token'], credentials['refresh_token'])

		client.set_user_auth(credentials['access_token'], credentials['refresh_token'])

	except IOError:

		client = ImgurClient(client_id, client_secret)
		
		pin = None
		if pin is None:
			# Authorization flow, pin example (see docs for other auth types)
			authorization_url = client.get_auth_url('pin')
			
			# ... redirect user to `authorization_url`, obtain pin (or code or token) ...
			webbrowser.open(authorization_url)
			print("Please enter the pin:")
			pin = raw_input()

		credentials = client.authorize(pin, 'pin')
		client.set_user_auth(credentials['access_token'], credentials['refresh_token'])

		print("access token: [%s]" % credentials['access_token'])
		print("refresh token: [%s]" % credentials['refresh_token'])

		with open(cfilepath, 'w') as f:
			json.dump(credentials, f)

	print("You are now authorized")
	return client

def uploadimages(imagelist, albumid):

	# this requires us to call authenticate first!
	#client = authenticate(credentialsfilepath)

	imagedata = []
	for imagepath in imagelist:
		result = client.upload_from_path(imagepath, anon=False)
		imagedata.append(result)

	imageids = [data['id'] for data in imagedata]
	print("imageids:", imageids)
	imagedeletehashes = [data['deletehash'] for data in imagedata]
	print("imagedeletehashes:", imagedeletehashes)

	if albumid is None:
		albumspec = {
			'privacy': 'hidden',
			#'ids': imageids,
			#'deletehashes': imagedeletehashes,
		}
		if title is not None:
			albumspec['title'] = title

		albumdata = client.create_album(albumspec)
		print(albumdata)
		albumid = albumdata['id']

	print("album url: https://imgur.com/a/%s" % albumid)
	client.album_add_images(albumid, imageids)

	# each data in imagedata has 
	# - "id": the id of the uploaded image
	# - "link": the url of the uploaded image
	return imagedata


def usage(code, progname, message):
	if message:
		print(message)
	print("""\
Usage: %s [-n/--dryrun] [-d/--debug] [-v/--verbose] [-h/--help] <IMAGEPATHS>...
where
	--dryrun: runs the program without actually uploading anything to imgur.
		Authentication is performed, and files are searched for.
	--debug: spits out debug information to help isolate a problem.
		Enables the python debugger
	--verbose: increases the verbosity of the program. Can be used more than once.
	--help: spits out this help and exits
	<IMAGEPATHS>: the list of images that should be uploaded.
		This can contain wild chars, to glob files together
		This is a required argument. At least one image must be specified
""") % progname,
	sys.exit(code)


def main(argv):

	dryrun = False
	imagelist = []
	debug = False
	verbose = 0

	albumid = None
	query = False
	title = 'test post'
	sanity = ''
	cfilepath = credentialsfilepath

	try:
		optlist, args = getopt.gnu_getopt(argv[1:], 'c:a:qt:s:ndvh', ['credentials', 'album', 'query', 'title=', 'sanity=', 'dryrun', 'debug', 'verbose', 'help'])
	except getopt.GetoptError as err:
		usage(-2, argv[0], err)
	for opt, arg in optlist:
		if opt in ('-h', '--help'):
			usage(0, argv[0], '')
		elif opt in ('-c', '--credentials'):
			cfilepath = arg
		elif opt in ('-a', '--album'):
			albumid = arg
		elif opt in ('-q', '--query'):
			query = True
		elif opt in ('-t', '--title'):
			title = arg
		elif opt in ('-s', '--sanity'):
			sanity = arg
		elif opt in ('-d', '--debug'):
			debug = True
		elif opt in ('-v', '--verbose'):
			verbose += 1
		elif opt in ('-n', '--dryrun'):
			dryrun = True
		else:
			usage(-1, argv[0], "unknown argument [%s]" % opt)

	if dryrun:
		print("doing dryrun")
	if sanity:
		print("doing sanity", sanity)

	imagelist = sum([glob.glob(arg) for arg in args], [])
	cfilepath = os.path.expanduser(cfilepath)

	if sanity:
		fail = False
		width, height = [int(i) for i in sanity.split('x')]
		for imagepath in imagelist:
			im = Image.open(imagepath)
			if im.size[0] > width or im.size[1] > height:
				print("sanity check fail: [%s] has insane size" % imagepath, im.size)
				fail = True
			else:
				print("[%s] is sane" % imagepath)
		if fail:
			sys.exit(-1)

	client = authenticate(cfilepath)

	if query:
		if albumid is None:
			usage(-1, argv[0], "[query] parameter requires [albumid]")
		images = client.get_album_images(albumid)
		#print(images)
		for image in images:
			print(image.link)
		sys.exit(0)

	if not imagelist:
		usage(-1, argv[0], 'Missing image list')

	if dryrun:
		print(imagelist)
		sys.exit(0)

	imagedata = uploadimages(imagelist, albumid)
	for path, data in zip(imagelist, imagedata):
		print("[img]%s[/img]" % data['link'], path)

if __name__ == "__main__":
	main(sys.argv)




