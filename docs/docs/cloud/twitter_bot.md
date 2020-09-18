# Twitter Bot

Every time the website updates, it sends out a tweet.

## First Time Setup

Follow these steps to set up the Twitter bot for the first time, such as on a new Twitter account.

1. Create a [Twitter](https://twitter.com/) account that will host the bot, or login to an account you already have that you want to send automated tweets from.

2. Go to [https://apps.twitter.com/](https://apps.twitter.com/) and sign up for a development account. Note that you will need both a valid phone number and a valid email tied to the developer account in order to use development features.

???+ note
    You will have to wait an hour or two for Twitter.com to get back to you and approve your developer account.

3. Once you are approved, go to the [Twitter Developer Portal](https://developer.twitter.com/). Click on the app you created, and in the `Settings` tab, ensure that the App permissions are set to *Read and Write* instead of only *Read*.

???+ tip
    If at some point during step 3 Twitter starts throwing API keys at you, ignore it for now. We'll get all the keys we need in next couple steps.

4. In the code base, use the `VAULT_PASSWORD` to unzip the `vault.7z` manually. You should have a file called `secrets.json`. Open up `secrets.json` in the plaintext editor of your choosing.

???+ danger
    Make sure that you delete the unencrpyted, unarchived version of the `secrets.json` file after you are done with it.

5. Now go back to your browser with the Twitter Developer Portal. At the top of the screen, flip to the `Keys and tokens`. Now it's time to go through the dashboard and get your copy+paste ready. We will be inserting these values into the `secrets.json` (remember to wrap the keys in double quotes `"like this"` when you insert them).

  - The `API Key & Secret` should should go in the corresponding fields for `"api_key": "..."` and `"api_key_secret": "..."`.
  - The `Bearer Token` should go in the field `"bearer_token": "..."`.
  - The `Access Token & Secret` should go in the corresponding fields for `"access_token": "..."` and `"access_token_secret": "..."`. _But first, you will need to regenerate the `Access Token & Secret` so that it has both read and write permissions._

???+ success
    The `secrets.json` file should look something like this, with the ellipses replacing the actual values:
    
    ```json
    {
        "SECRET_KEY": "...",
        "HOBOLINK_AUTH": {
           "password": "...",
           "user": "...",
           "token": "..."
        },
        "TWITTER_AUTH": {
            "api_key": "...",
            "api_key_secret": "...",
            "bearer_token": "...",
            "access_token": "...",
            "access_token_secret": "..."
        }
    }
    ```

6. Rezip the file. Enter the `VAULT_PASSWORD` when prompted (happens twice).

```shell
cd flagging_site
7z a -p vault.7z secrets.json
cd ..
```

7. Delete delete the unencrpyted, unarchived version of the `secrets.json` file.
