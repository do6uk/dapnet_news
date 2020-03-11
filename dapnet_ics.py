#!/usr/bin/env python3
# -*- coding: utf-8 -*-

## parsing ics-file an sending news to dapnet rubric
##
## 20200311 do6uk

from icalendar import Calendar, Event
from datetime import datetime
from dateutil import tz
import argparse
import requests
import time
import json
import sys


## CONFIG

# replace words/chars in summary-field
repl_chars = {"ä":"ae", "ö":"oe", "ü":"ue", "Ä":"Ae", "Ö":"Oe", "Ü":"Ue", "ß":"ss"}
repl_words = {"Jugendversammlung":"Ju-Vers.", "Mitgliederversammlung":"Mtgl-Vers.", "Distriktsversammlung":"Dist-Vers.", "mit":"+", "Protokoll":"Prot."}

# url to ics-file
ics_url = "http://server.tld/events.ics"

# url to dapnet-core
dapnet_url = "http://www.hampager.de:8080"
# basic_auth
dapnet_auth = ('#yourcallsign#','#yourkey#')
# rubric-name like given at hampager.de
dapnet_rub = 'null'
# rubric-owner to set
dapnet_owner = '#yourcall#'

# headline-message / if empty it will not be send
msg_headline = "## Events ##"
# after this news-number at rubric we will start to send
msg_offset = 5
# how many messages we want to send
msg_max = 5


## MAIN CODE - do not edit below this point

cli_parse = argparse.ArgumentParser(description='parsing a ics-file to send events as dapnet-rubric-content')
cli_parse.add_argument('-l','--local', action='store_true', help='do not send news to dapnet-core')
cli_parse.add_argument('-v','--verbose', action='store_true', help='print to screen what happens')
cli_parse.add_argument('-s','--silent', action='store_true', help='do not print anything')
cli_parse.add_argument('-f','--force', action='store_true', help='(unused option)')
cli_parse.add_argument('-j','--json', action='store_true', help='saving uploaded data as json')
cli_args = cli_parse.parse_args()

heute = []
woche = []
vorschau = []
dapnet_msg = []

if cli_args.silent:
	cli_args.verbose = False
else:
	print('## running',sys.argv[0])

if not cli_args.silent:
	print('## downloading ics-file',ics_url)

r = requests.get(ics_url, allow_redirects=True)

if cli_args.verbose:
	print('\n<ICS>\n')
	print(r.content)
	print('\n<EOF>\n')
	#open('termine_h.ics', 'wb').write(r.content)

if not cli_args.silent:
	print('## parsing with icalendar')

ical = Calendar.from_ical(r.content)
ts_now = time.time()
ts_today = time.mktime(datetime.today().date().timetuple())
today = datetime.today()
from_zone = tz.tzutc()
to_zone = tz.tzlocal()

items = ical.walk()
items = filter(lambda c: c.name == 'VEVENT', items)
items = filter(lambda c: time.mktime(c.get('dtstart').dt.timetuple()) >= ts_today, items)
items = sorted(items, key=lambda c: time.mktime(c.get('dtstart').dt.timetuple()), reverse=False)

if not cli_args.silent:
	print('## collecting comming events')

for item in items:
	summary = item.get('summary')
	location = item.get('location')
	description = item.get('description')
	startdt = item.get('dtstart').dt
	exdate = item.get('exdate')
	rrule = item.get('rrule')

	for key in repl_words.keys():
		summary = summary.replace(key, repl_words[key])

	for key in repl_chars.keys():
		summary = summary.replace(key, repl_chars[key])
		location = location.replace(key, repl_chars[key])
		description = description.replace(key, repl_chars[key])

	if location != '':
		location = '@ '+location

	if description != '':
		description = '# '+description

	try:
		# versuche startdt in Datum zu wandeln
		idate = startdt.date()
		startdt = startdt.replace(tzinfo=from_zone)
		startdt_local = startdt.astimezone(to_zone)
	except:
		# startdt ist schon ein Datum
		idate = startdt
		startdt_local = startdt

	if startdt_local.strftime("%H:%M") == '00:00':
		start = startdt_local.strftime("%d.%m.%y")
	else:
		start = startdt_local.strftime("%d.%m.%y %H:%M")

	msg = "{0} {1} {2}".format(start, summary, location)

	if len(start) + len(summary) + len(location) < 60:
		msg += description

	mlen = len(msg)

	if mlen <= 80:
		## lassen wir so
		pass
	else:
		msg = msg[0:78]+'..'

	if cli_args.verbose:
		print(msg)

	if idate == today.date():
		if cli_args.verbose:
			print(' .. is today')
		heute.append(msg)
	#elif today.weekday() == 1 and time.mktime(startdt_local.timetuple()) <= ts_now + (86400 * 7):
	#	# am Tag X eine Wochenvorschau erstellen / Mo = 0
	#	if cli_args.verbose:
	#		print(' .. is this week')
	#	woche.append(msg)
	else:
		if cli_args.verbose:
			print(' .. is comming up')
		vorschau.append(msg)

if not cli_args.silent:
	print('## preparing events for dapnet')

msgcount = 0

if msg_headline != '':
	msgcount += 1
	msg = "## {0} # {1} via DB0USD ##".format(msg_headline, today.strftime("%d.%m.%y %H:%M"))
	if cli_args.verbose:
		print(msgcount, msg)
	dapnet_msg.append(msg)

if cli_args.verbose:
	print('\nHeute \n')

if heute == []:
	if cli_args.verbose:
		print('no milk today ;-)')
	heute.append('## Heute keine Termine ;-) mehr Zeit zum Funken ## Terminvorschau: ')

for msg in heute:
	if msgcount >= msg_max:
		break
	msgcount += 1
	if cli_args.verbose:
		print(msgcount, msg)
	dapnet_msg.append(msg)

#if cli_args.verbose:
#	print('\nWoche\n')
#for msg in woche:
#	if msgcount >= msg_max:
#		break
#	msgcount += 1
#	if cli_args.verbose:
#		print(msgcount, msg)
#	dapnet_msg.append(msg)

if cli_args.verbose:
	print('\nVorschau\n')
for msg in vorschau:
	if msgcount >= msg_max:
		break
	msgcount += 1
	if cli_args.verbose:
		print(msgcount, msg)
	dapnet_msg.append(msg)

if not cli_args.silent:
	print('## generating rubric-data')

msgnumber = 0
dapnet_json = []

if not cli_args.silent:
	if not cli_args.local:
		print('\n## sending events to DAPNET-Core',dapnet_url,'\n')
	else:
		print('\n## dumping events as JSON\n')

for msg in dapnet_msg:
	msgnumber += 1
	msgjson = {"text": msg, "rubricName":dapnet_rub, "number": msgnumber+msg_offset, "ownerName": dapnet_owner}
	dapnet_json.append(msgjson)

	if not cli_args.local:
		if cli_args.verbose:
			print('sending request')
		r_upload = requests.post(dapnet_url+'/news?rubricName='+dapnet_rub, auth = dapnet_auth, json = msgjson)
		if not cli_args.silent:
			print('<{0:02d}> {1} [{2}]'.format(msgnumber+msg_offset,msg,r_upload.status_code))
	else:
		if not cli_args.silent:
			print('<{0:02d}> {1} [OK]'.format(msgnumber+msg_offset,msg))


if cli_args.local or cli_args.json:
	if cli_args.verbose:
		print('\n<JSON>\n')
		print(dapnet_json)
		print('\n<EOF>\n')

	with open('dapnet_ics.json', 'w', encoding='utf-8') as f:
		json.dump(dapnet_json, f, ensure_ascii=False, indent=4)

	if not cli_args.silent:
		print('\n## json written to dapnet_ics.json')
