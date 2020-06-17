"""
This is a basic script to output a message to twitter
User must input public and private key from Consumer
and access. They will be imported from keys file

Future Plans: 
Allow more functionality allowing user input

"""

import tweepy

# Constants for secret and public keys

CONSUMER_KEY = '' 
CONSUMER_SECRET = ''
ACCESS_KEY = ''
ACCESS_SECRET = ''

def post_tweet(msg): 
    """
        Posts tweet onto twitter handle

        arg: accept string message msg

        returns: string message that have been inputed
    """

    # Authenticates using consumer key and secret
    auth=tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)

    # Authenticates using access key and secret
    auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)
    api = tweepy.API(auth)


    #print message on terminal and update status 
    # to twitter handle
    print ('Tweeting' + msg) 
    api.update_status(msg)

    return msg 