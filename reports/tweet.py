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
        body = '{} - {}\n----\n{}'.format(incident.title,
                                          incident.station.name,
                                          incident.get_url)
        # short_desc = incident.title[:140-(len(body) - 5)]

        self.api.PostUpdate(body)
