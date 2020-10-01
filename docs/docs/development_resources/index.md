# Stack

## Project History

Traditionally, the CRWA Flagging Program was hosted on a PHP-built website that hosted a predictive model and ran it. However, that website was out of commission due to some bugs and the CRWA's lack of PHP development resources.

We at Code for Boston attempted to fix the website, although we have had trouble maintaining a steady stream of PHP expertise, so we rebuilt the website from scratch in Python. The project's source code is available [on GitHub](https://github.com/codeforboston/flagging/wiki), and the docs we used for project management and some dev stuff are available in [the repo's wiki](https://github.com/codeforboston/flagging/wiki).

## Why Python?

Python proves to be an excellent choice for the development of this website. Due to how the CRWA tends to staff its team (academics and scientists), Python is the most viable language that a website can be built in while still being maintainable by the CRWA. The two most popular coding languages in academia are R and Python. You can't really build a website in R (you technically can, but really really shouldn't for a lot of reasons). So the next best option is Python.

Even if the CRWA does not staff people based on their Python knowledge (we do not expect that they will do this), they are very likely have connections to various people who know Python. It is unlikely that the CRWA will have as many direct ties to people who have Javascript or PHP knowledge. Because long-term maintainability is such a high priority, Python is the sensible technical solution.

Not only is Python way more popular than PHP in academia, it's [the most popular programming language](http://pypl.github.io/PYPL.html) _in general_. This means that Python is a natural fit for any organization's coding projects that do not have specialized needs for a particular coding language.

## Why Flask?

Once we have decided on Python for web development, we need to make a determination on whether to use Django or Flask, the two leading frameworks for building websites in Python.

Django is designed for much more complicated websites than what we would be building. Django has its own idiom that takes a lot of time to learn and get used to. On the other hand, Flask is a very simple and lightweight framework built mainly around the use of its "`app.route()`" decorator.

## Why Heroku?

Heroku's main advantage is that we can run it for free; the CRWA does not want to spend money if they can avoid doing so.

One alternative was [Google Cloud](https://cloud.google.com/free/docs/gcp-free-tier#always-free), specifically the [Google App Engine](https://cloud.google.com/appengine/docs/standard/python3/building-app).

We did not do this mainly as it is more work to set up for developers and controlling costs requires extra care. E.g. the always free tier of Google Cloud still requires users to plug in a payment method. Developers who want to test Google Cloud functionality would also run into some of those limitations too, depending on their past history with Google Cloud.

With that said, Heroku does provide some excellent benefits focused around how lightweight it is. Google Cloud is not shy about the fact that it can host massive enterprise websites with extremely complicated infrastructural needs. Don't get me wrong: Heroku can host large websites too. But Heroku supports small to medium sites extremely well, and it is really nice for open source websites in particular.

- Heroku is less opinionated about how you manage your website, whereas Google Cloud products tend to push you toward Google's various Python integrations and APIs.
- Google Cloud is a behemoth of various services that can overwhelm users, whereas Heroku is conceptually easier to understand.
- Heroku integrates much more nicely into Flask's extensive use of CLIs. For example, Heroku's task scheduler tool (which is very easy to set up) can simply run a command line script built in Flask. Google App Engine lets you do a simple cron job setup that [sends GET requests to your app](https://cloud.google.com/appengine/docs/flexible/python/scheduling-jobs-with-cron-yaml), but doing something that doesn't publicly expose the interface requires use of [three additional services](https://cloud.google.com/python/getting-started/background-processing): Pub/Sub, Firestore, and Cloud Scheduler.
- We want to publicly host this website, but we don't want to expose the keys we use for various things. This is a bit easier to do with Heroku, as it has the concept of an environment that lives on the instance's memory and can be set through the CLI. Google App Engine lets you configure the environment [only](https://cloud.google.com/appengine/docs/flexible/python/reference/app-yaml) through `app.yaml`, which is an issue because it means we'd need to gitignore the `app.yaml`. (We want to just gitignore the keys, not the whole cloud deployment config!)

???+ warning
    If you ever want to run this website on Google App Engine, you'll have to make some changes to the repository (such as adding an `app.yaml`), and it may also involve making changes to the code-- mainly the data backend and the task scheduler interface.

## Why Pandas?

We made the decision to use Pandas to manipulate data in the backend of the website because it has an interface that should feel familiar to users of Stata, R, or other statistical software packages commonly used by scientists and academics. This ultimately helps with the maintainability of the website for its intended audience. Data manipulation in SQL can sometimes be unintuitive and require advanced trickery (CTEs, window functions) compared to Pandas code that achieves the same results. Additionally, SQL code tends to be formatted in a non-chronological way, e.g. subqueries run before the query that references them, but occur somewhere in the middle of a query. This isn't hard if you use SQL a bit, but it's not intuitive until you've done a bit of SQL.

It's true that Pandas is not as efficient as SQL, but we're not processing millions of rows of data, we're only processing a few hundred rows at a time and at infrequent intervals. (And even if efficiency was a concern, we'd sooner use something like [Dask](https://dask.org/) than SQL.)

One possible downside of Pandas compared to SQL is that SQL has been around for a very long time, and is more of a "standardized" thing than Pandas is or perhaps ever will be. We went with the choice for Pandas after discussing it with some academic friends, but we are aware that in the non-academic world, there are more people who know SQL than Pandas.

We do use SQL in this website, but primarily to store and retrieve data and to access some features that integrate nicely with the SQLAlchemy ORM (notably the Flask-Admin extension).
