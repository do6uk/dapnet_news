#!/usr/bin/env python3
# -*- coding: utf-8 -*-

## parsing rss-feed to send news to dapnet rubric
##
## 20200311 do6uk

from datetime import datetime
from dateutil import tz
import argparse
import requests
import time
import json
import sys
import feedparser


## CONFIG

# replace words/chars in summary-field
repl_chars = {"ä":"ae", "ö":"oe", "ü":"ue", "Ä":"Ae", "Ö":"Oe", "Ü":"Ue", "ß":"ss"}
repl_words = {}

# url to rss-feed
rss_url = "http://server.tld/rssfeed.xml"

# url to dapnet-core
dapnet_url = "http://www.hampager.de:8080"
# basic_auth
dapnet_auth = ('#yourcallsign#','#yourkey#')
# rubric-name like given at hampager.de
dapnet_rub = 'null'
# rubric-owner to set
dapnet_owner = '#yourcallsign#'

# headline-message / if empty it will not be sent
msg_headline = ""
# after this news-number at rubric we will start to send
msg_offset = 4
# how many messages we want to send
msg_max = 1


## MAIN CODE - do not edit below this point

cli_parse = argparse.ArgumentParser(description='parsing a rss-feed to send news as dapnet-rubric-content')
cli_parse.add_argument('-l','--local', action='store_true', help='do not send news to dapnet-core')
cli_parse.add_argument('-v','--verbose', action='store_true', help='print to screen what happens')
cli_parse.add_argument('-s','--silent', action='store_true', help='do not print anything')
cli_parse.add_argument('-f','--force', action='store_true', help='send news anyway (default: only send if new item)')
cli_parse.add_argument('-j','--json', action='store_true', help='saving uploaded data as json')
cli_args = cli_parse.parse_args()

if cli_args.silent:
	cli_args.verbose = False
else:
	print('## running',sys.argv[0])

try:
	with open('dapnet_rss.latest','r',encoding='utf-8') as f:
		latest = json.load(f)

	if cli_args.verbose:
		print('## read latest news from dapnet_rss.latest')
		print(latest)
except:
	if cli_args.verbose:
		print('## dapnet_rss.latest NOT found')
	latest = {}

feed = feedparser.parse(rss_url)
if cli_args.verbose:
	print('\n<RSS:CHANNEL>\n')
	print(feed.feed)
	print('\n<EOF>\n')

feed_time = time.strptime(feed.feed.published, '%a, %d %b %Y %H:%M:%S %z')
feed_humantime = time.strftime('%d.%m.%Y %H:%M:%S',feed_time)
feed_ts = time.mktime(feed_time)

if not cli_args.silent:
	print('## parsing rss-feed')
if cli_args.verbose:
	print(feed.feed.generator, feed_humantime, feed_ts)

if not cli_args.silent:
	print('## parsing feed items')
if cli_args.verbose:
	print('\n<RSS:ITEM>\n')
	print(feed.entries)
	print('\n<EOF>\n')

newscount = 0
upload_ok = False
dapnet_json = []

if not cli_args.local:
	if not cli_args.silent:
		print('\n## sending news to DAPNET-Core',dapnet_url,'\n')
else:
	if not cli_args.silent:
		print('\n## dumping news as JSON\n')


for item in feed.entries:
	newscount += 1
	item_time = time.strptime(item.published, '%a, %d %b %Y %H:%M:%S %z')
	item_humantime = time.strftime('%d.%m.%y %H:%M',item_time)
	item_ts = time.mktime(item_time)
	item_title = item.title

	for key in repl_words.keys():
		item_title = item_title.replace(key, repl_words[key])

	for key in repl_chars.keys():
		item_title = item_title.replace(key, repl_chars[key])

	if cli_args.verbose:
		print('>',item.title,'@',item_humantime)

	if newscount == 1:
		latest_news = {'guid': item.guid, 'title': item.title, 'timestamp': item_ts}
		if latest == latest_news and not cli_args.force:
			if not cli_args.silent:
				print('## no fresh news in rss')
			break
		elif latest == latest_news and cli_args.force and not cli_args.silent:
			print('## no fresh news, but will send anyway (--force)')

	msg = '## NEWS-Distrikt H > {0} @ {1}'.format(item_title,item_humantime)
	mlen = len(msg)
	if mlen <= 80:
		## lassen wir so
		pass
	else:
		msg = msg[0:78]+'..'

	if cli_args.verbose:
		print('<{0:02d}> {1} ({2})'.format(newscount+msg_offset, msg, mlen))
	msgjson = {"text": msg, "rubricName": dapnet_rub, "number": newscount+msg_offset, "ownerName": dapnet_owner}
	dapnet_json.append(msgjson)

	if not cli_args.local:
		r_upload = requests.post(dapnet_url+'/news?rubricName='+dapnet_rub, auth = dapnet_auth, json = msgjson)
		if not cli_args.silent:
			print('<{0:02d}> {1} [{2}]'.format(newscount+msg_offset,msg,r_upload.status_code))
		if r_upload.status_code == 201:
			#if True:
			upload_ok = True
	else:
		if not cli_args.silent:
			print('<{0:02d}> {1} [OK]'.format(newscount+msg_offset,msg))

	if newscount == msg_max:
		if cli_args.verbose:
			print('## reached msg_max',msg_max)
		break

if upload_ok:
	with open('dapnet_rss.latest','w', encoding='utf-8') as f:
		json.dump(latest_news,f,ensure_ascii=False, indent=4)
		if cli_args.verbose:
			print('## saving latest news in dapnet_rss.latest')
			print(latest_news)

if cli_args.local or cli_args.json:
	if cli_args.verbose:
		print('\n<JSON>\n')
		print(dapnet_json)
		print('\n<EOF>\n')

	with open('dapnet_rss.json', 'w', encoding='utf-8') as f:
		json.dump(dapnet_json, f, ensure_ascii=False, indent=4)

	if not cli_args.silent:
		print('\n## json written to dapnet_rss.json')
