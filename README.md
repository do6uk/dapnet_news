# dapnet_news

These scripts will parse external data and push it into a dapnet-rubric

* **dapnet_ics.py** sending events from icalendar-files
* **dapnet_rss.py** sending news from rss-feed


## requirements

* Python3
* pip3 install icalendar (used by dapnet_ics.py)
* pip3 install feedparser (used by dapnet_rss.py)


## get them running

* put in your dapnet-credentials under **## CONFIG**
* define a data source (rss_url / ics_url)
* define a rubric-name as given at dapnet-core
* define a owner-callsign to be set in the news
* set *msg_offset* to decide after which *Number* at the rubric we start to send the news
* set *msg_max* to decide how many news we will send


## cli-arguments

**--local *or* -l**  don't send news to dapnet (for testing)

**--verbose *or* -v**  we will see what happens

**--silent *or* -s**  we won't see anything

**--force *or* -f**  force an upload even if no new data is present

**--json *or* -j**  save uploaded data as .json (for checking what has been uploaded)


## dapnet_ics.py

This will fetch a .ics-file from a webserver and parse it for upcomming events. 
Actually there is no check, what we uploaded last time, so the script will always upload all events.
You would like to run this script once oder twice a day.


## dapnet_rss.py

This will fetch a rss.xml from a webserver and parse it for latest news.
It is checking, what was latest news at last runtime and only upload new news, except you are overriding by *--force*.
You would like to run this script @hourly.
