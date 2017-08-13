import twitter

from crime import settings


class TwitterNotConfigured(Exception):
    """Exception raised when Twitter is not configured."""
    pass


class Twitter(object):
    def __init__(self):
        self.api = None

    def connect(self):
        self.api = twitter.Api(
            consumer_key=settings.get_secret('TWITTER_CONSUMER_KEY'),
            consumer_secret=settings.get_secret('TWITTER_CONSUMER_SECRET'),
            access_token_key=settings.get_secret('TWITTER_ACCESS_TOKEN_KEY'),
            access_token_secret=settings.get_secret(
                'TWITTER_ACCESS_TOKEN_SECRET'),
        )

    def post_incident(self, incident):
        tweet_text = "{} {}".format(incident.tweet_text, incident.get_url)
        print "Tweet text: {}".format(tweet_text)
        if self.api is not None:
            self.api.PostUpdate(tweet_text)
        else:
            raise TwitterNotConfigured()
