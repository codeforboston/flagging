# Front-End

## The Flask Ecosystem

The flagging website is build primarily in [Flask](https://flask.palletsprojects.com/), which has a reputation as one of the simplest web frameworks in the Python world.

You can see for yourself how easy Flask is: here is a "hello world" you can build in Flask that works by simply running `python app.py`, then pointing your browser to `http://127.0.0.1/`:

```python
# Contents of file "app.py"
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home_page():
    return 'Hello, world!'

if __name__ == '__main__':
    app.run()
```

Flask uses a concept called "blueprints," which are like miniature apps that join to the main app.

We store our frontend as a blueprint named `flagging`, and our REST API as a blueprint named `api`. These blueprints handle the logic of rendering the web pages.

The web pages are built using "[Jinja templates](https://jinja.palletsprojects.com/en/2.11.x/)." One way to think of Jinja is that it's a way to add things like "for" loops and Python variables into an HTML page or other plain text file.

## Flagging Website Templates

### Naming convention for files

In general, we try to use the following naming convention:

- Templates rendered directly by the endpoints are named as obviously as possible. For example, the `/about` page is rendered by a function named `about()`, and the template it renders is `about.html`.
- Things _not_ rendered directly, such as partial components or the base template, start with an underscore. This loosely follows the Python convention of having the single leading underscore indicate the value is "for internal use only."
Our core website inherits from `_base.html`.

The `/flagging_site/templates/admin` folder is the main exception to this. This folder is structured and named in a specific way to mimic Flask-Admin's template schema and (occasionally) overwrite some of its templates.

All of the front-end templates for the core website "extend" the `_base.html` template. You can think of `_base.html` as defining the scaffolding of the website.

### Misc. templating notes

- We intentionally avoid Javascript as much as we can to help minimize maintenance prerequisites for the website.
- `_flag_widget_v##.html` is imported into both the `/flags` widget and the home page `/`.
  - In the filename, `##` is a 2-digit integer; include the leading zeroes!
  - You can define the default widget number to use in the config variable `DEFAULT_WIDGET_VERSION`. (No need to include the leading zeroes when defining the default in `config.py`, a normal integer will do).
- As the app spins up, we add a couple things to the Jinja template environment (see the function `register_jinja_env()` inside of `app.py`):
  - MD5 hashes for static file URLs to assist with browser caching.
  - The contents of some SVG files. Although we store them in the `/static` folder, you get to do more things with the CSS when you render them directly in the HTML instead of using `<img src="...">`.
  - A function called `get_widget_filename()` that chooses the default flagging widget version to render.

## Caching

Our web pages only change once every X hours. As of writing, X is 6 hours.

It doesn't make sense to go through all the labor of processing a page 1,000 times in a row if we know each time the page won't change.

We use a simple cache-aside design for our frontend pages:

- The first time a page is loaded, if it is not in the cache, then build the page.
- If the page is loaded subsequently, 
- The _entire_ cache is cleared whenever a change to the database is made, either via the admin panel or via the `update_db()` command.
- The cache entries have natural expiration (time to live, or "ttl") of 7 hours. As long as the scheduler works properly, cache entries should never expire on their own, though.

???+ note
    Yes, we clear the _entire_ cache after _every_ database update, even when the page we cached would hot have been affected by the database change.
    
    It's not worth maintaining code for nuanced cache-clearing logic, where it only clears the cache for a page that would have been affected by a change. We get 99% of the performance boost and save ourselves a massive debugging headache.

In production, we use [Redis](https://redis.io/topics/lru-cache) for server-side caching. Heroku automatically gives us a `REDIS_URL` environment variable that we can reference, and the Python packages `Flask-Caching` and `redis` handle the rest.

In development and testing, we use Werkzeug's [SimpleCache](https://werkzeug.palletsprojects.com/en/0.14.x/contrib/cache/). The benefit of the SimpleCache for dev and test environments is it doesn't require installing anything extra to run. But, it really is not well-suited for production purposes.

## Swagger and the Public Flagging REST API

???+ tip
    You can play around with our Swagger extension [here]({{ flagging_website_url }}/api/docs) in production.

Swagger is the organization behind the [OpenAPI Specification](https://swagger.io/specification/), or "OAS."

OAS is very "meta" and easier to explain via example. If my endpoint always returns a positive integer labeled "foo," then these would all be valid responses:
 
- `#!json {"foo": 5}`
- `#!json {"foo": 123}`
- `#!json {"foo": 50000}`

But something like `{"foo": "not a number"}` would be an _invalid_ response, according to what I just said.

As a developer, I might want to tell other "my endpoint always behaves this way-- it returns positive integers named 'foo'. And it does not return text or decimals or anything else." There are a few ways to do that, but one commonly accepted way is OAS-- a way to standardize how you describe your web API endpoint's behavior.

You will see references in the code to Swagger and "swag," and you'll also see some YAML files inside the `/flagging_site/blueprints` folder. All of that stuff is related to the OAS specification, and we've implemented it with a community-run extension called [Flasgger](https://github.com/flasgger/flasgger).
