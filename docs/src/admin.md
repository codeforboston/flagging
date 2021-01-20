# Website Administration

## Admin Panel

???+ Note
    This section discusses how to use the admin panel for the website. For how to set up the admin page username and password during deployment, see the [Heroku deployment](cloud/heroku_deployment.md) documentation.

The admin panel is used to do the following:
 
- Manually override the model outputs during events and advisories that would adversely effect the river quality.
- Set a custom message that shows on the home page alongside the flags.
- Manually update the database.
- Download the data as a CSV, including downloading up to 90 days worth of data at a time.

You can reach the admin panel by going to `/admin` after the URL for the flagging website homepage.

You will be asked a username and password, which will be provided to you by the person who deployed the website. Enter the correct credentials to enter the admin panel.

???+ note
    In "development" mode, the default username is `admin` and the password is `password`.
    
    In production, the environment variables `BASIC_AUTH_USERNAME` and `BASIC_AUTH_PASSWORD` are used to set the credentials. You can always check what they are in the "Settings" tab of the Heroku dashboard.

???+ warning
    In production, the admin panel password should be long, random, and unique:
    
    - Long and random because there is no brute force protection implemented on the website.
    - Unique because the password is stored in plain text.
    
    You can use a Python script such as this to generate a password appropraite for the website:
    
    ```python
    import string
    import random
    
    chars = list(map(str, [*string.ascii_letters, *range(10)]))
    password = ''.join([str(random.choice(chars)) for i in range(50)])
    
    print(password)
    ```
    
    For all intents and purposes, a password generated like this is effectively impossible to brute force: There are more possible 50 character alphanumeric passwords than there are atoms in the universe (62^50 > 10^81).
