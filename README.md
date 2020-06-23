# Flagging Website

This is the code base for the [Charles River Watershed Association's](https://crwa.org/) ("CRWA") flagging website. The flagging website hosts an interface for the CRWA's staff to monitor the outputs of a predictive model that determines whether it is reasonably safe to swim or boat in the Charles River.

This code base is built in Python 3.7+ and utilizes the Flask library heavily. The website can be run locally in development mode, and it can be deployed to Heroku using Gunicorn.

## For Developers

Please read the [Flagging Website wiki](https://github.com/codeforboston/flagging/wiki) for on-boarding documents, code style guide, and development requirements.

## Setup (Dev)

These are the steps to set the code up in development mode.

**On Windows:** open up a Command Prompt terminal window (the default in PyCharm on Windows), point the terminal to the project directory if it's not already there, and enter:

```commandline
run_windows_dev
```

If you are in PowerShell (default VSC terminal), use `start-process run_windows_dev.bat` instead.

**On OSX or Linux:** open up a Bash terminal, and in the project directory enter:

```shell script
sh run_unix_dev.sh
```

After you run the script for your respective OS, it will ask you if you want to use online mode. If you do not have the "vault password," say yes (`y`)

After that, it will ask if you have the vault password. If you do, enter it here. If not, you can skip this.

Note that the website will _not_ without either the vault password or offline mode turned on; you must do one or the other.

## Deploy

1. Download Heroku.

2. Set the vault password:

```shell script
heroku config:set VAULT_PASSWORD=replace_me_with_pw
```

3. Everything else should be set:

```shell script
heroku create crwa-flagging-staging
git push heroku master
```

## Run tests

Tests are written in Pytest. To run tests, run the following on your command line:

```shell script
python -m pytest ./tests -s
```

Note: the test may require you to enter the vault password if it is not already in your environment variables.
