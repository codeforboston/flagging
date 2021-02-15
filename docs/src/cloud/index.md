# Overview

The flagging website is designed to be hosted on [Heroku](https://heroku.com/).

The full cloud deployment depends not only on Heroku but also Twitter's development API. The Twitter bot only needs to be set up once and, notwithstanding exigent circumstances (losing the API key, migrating the bot, or handling a Twitter ban), the Twitter bot does not need any additional maintenance. Nevertheless, there is documentation for how to set up the Twitter bot [here](../twitter_bot).

???+ note
    Prior to one-click deployment, we setup the website configuration manually. You can see our guide on how to manually deploy [here](./manual_heroku_deployment). Note that it is missing the Redis database.
