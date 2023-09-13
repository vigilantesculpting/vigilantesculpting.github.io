#!/usr/bin/env python3

import datetime
import pytz
import sys

def now(tzname = "America/Los_Angeles"):

	try:
		tz = pytz.timezone(tzname)
	except pytz.exceptions.UnknownTimeZoneError as e:
		print(f"Unkown timezone [{tzname}]")
		print("Select one from the following:")
		print("\n".join(pytz.common_timezones))
		sys.exit(1)

	return datetime.datetime.now(tz)

if __name__ == "__main__":
	tzname = sys.argv[1]

	print(now(tzname).strftime("%Y-%m-%dT%H:%M:%S %z %Z"))


