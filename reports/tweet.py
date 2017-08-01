import datetime
import random
from urllib2 import urlopen

import twitter

from crime import settings



class Twitter:
    def __init__(self):
        self.api = None

    def connect(self):
        self.api = twitter.Api(
            consumer_key=settings.get_secret('TWITTER_CONSUMER_KEY'),
            consumer_secret=settings.get_secret('TWITTER_CONSUMER_SECRET'),
            access_token_key=settings.get_secret('TWITTER_ACCESS_TOKEN_KEY'),
            access_token_secret=settings.get_secret('TWITTER_ACCESS_TOKEN_SECRET'),
        )

    def post_incident(self, incident):
        f = urlopen('http://tinyurl.com/api-create.php?url={0}'.format(incident.get_url()))
        tiny_url = f.read()

        POST_LENGTH = 140

        body = '<BOD>\n----\nDetails @ {}'.format(tiny_url)
        short_desc = incident.title[:POST_LENGTH-(len(body) - 5)]
        body = body.replace('<BOD>', incident.title)

        self.api.PostUpdate(body)
