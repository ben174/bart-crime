import twitter

from crime import settings

class TwitterNotConfigured(Exception):
    """Exception raised when Twitter is not configured."""
    pass

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
        print "Tweet text: {}".format(incident.tweet_text)
        if self.api is not None:
            self.api.PostUpdate(incident.tweet_text)
        else:
            raise TwitterNotConfigured()
