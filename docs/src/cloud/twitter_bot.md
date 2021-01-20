# Twitter Bot

Every time the website updates, it sends out a tweet. In order for it to do that though, you need to set up a Twitter account.

## First Time Setup

Follow these steps to set up the Twitter bot for the first time, such as on a new Twitter account.

1. Create a [Twitter](https://twitter.com/) account that will host the bot, or login to an account you already have that you want to send automated tweets from.

2. Go to [https://apps.twitter.com/](https://apps.twitter.com/) and sign up for a development account. Note that you will need both a valid phone number and a valid email tied to the developer account in order to use development features.

???+ note
    You will have to wait an hour or two for Twitter.com to get back to you and approve your developer account.

3. While you are waiting, make sure you have a text file called `.env` in the root directory of the repo. If you do not, you can create it via the following commands:

=== "Windows (CMD)"
    ```shell
    type nul >.env
    ```

=== "OSX (Bash)"
    ```shell
    touch .env
    ```

4. Once you are approved by Twitter, go to the [Twitter Developer Portal](https://apps.twitter.com/). Click on the app you created, and in the `Settings` tab, ensure that the App permissions are set to *Read and Write* instead of only *Read*.

5. Now go back to your browser with the Twitter Developer Portal. At the top of the screen, flip to the `Keys and tokens`. Now it's time to go through the dashboard and get your copy+paste ready. We will be inserting these values into the `.env` file, which you can edit using a plain text editor such as Notepad or Sublime.

  - The `API Key & Secret` should should go in the corresponding fields for `TWITTER_API_KEY=?` and `TWITTER_API_KEY_SECRET=?`.
  - The `Bearer Token` should go in the field `TWITTER_BEARER_TOKEN=?`.
  - The `Access Token & Secret` should go in the corresponding fields for `TWITTER_ACCESS_TOKEN=?` and `TWITTER_ACCESS_TOKEN_SECRET=?`. _But first, you will need to regenerate the `Access Token & Secret` so that it has both read and write permissions._

???+ success
    The `.env` file should look something like this when you're done:
    
    ```
    TWITTER_API_KEY=T5jlO9KNtL2UyffM7s0UhYkks
    TWITTER_API_KEY_SECRET=O4Er0BNzyWWjyPcHxGjiDtFXh4zTYMJmWIGLUBKzaOePMKnhba
    TWITTER_BEARER_TOKEN=AAAAAAAAAAAAAAAAA3Gs6DHAAAAAAmVr9lhxSholbGiSGlE6gnCJo6XBmCQGo7yiTSZUffHO73NBHJ0CXdfYI4ysiD4mymI72uH88Gt
    TWITTER_ACCESS_TOKEN=gAcpWV4mToPvdijJUYRKV3UxGloMUmaDau5VbSb8LKSP3kCUPp
    TWITTER_ACCESS_TOKEN_SECRET=RskftNO5RqzZi1d5EOeNXgHpV
    ```
