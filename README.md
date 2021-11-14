# Flagging Website

![](app/static/images/og_preview.png)

**Our website is live at: [https://crwa-flagging.herokuapp.com/](https://crwa-flagging.herokuapp.com/)**

## Overview

This is the code base for the [Charles River Watershed Association's](https://crwa.org/) ("CRWA") flagging website. The flagging website hosts an interface for the CRWA's staff to monitor the outputs of a predictive model that determines whether it is reasonably safe to swim or boat in the Charles River.

This code base is built in Python 3.7+ and utilizes the Flask library heavily. The website can be run locally in development mode, and it can be deployed to Heroku using Gunicorn.

[![](../../workflows/tests/badge.svg)](../../actions)

## For Developers and Maintainers

**[Read our documentation here.](https://codeforboston.github.io/flagging/)** Our documentation contains information on everything related to the website, including [first time setup](https://codeforboston.github.io/flagging/setup/).

## Deploy to Heroku

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

**For demo mode deployment:** Set the `FLASK_ENV` variable to `demo` to run a version of this website in production using the demo data. Leave all the credentials fields blank.

**For full CRWA production deployment:** See the docs.

Note: Depending on how actively maintained this repo is, you may need to update `runtime.txt` by the time you read this. See [here](https://devcenter.heroku.com/articles/python-support#supported-runtimes) for supported Python runtimes.

## Credits

This website was built by volunteers at [Code for Boston](https://www.codeforboston.org/) in collaboration with the Charles River Watershed Association.
