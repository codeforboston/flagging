# Learning Resources

???+ tip
    Unless you want to overhaul the website or do some bugfixing, you _probably_ don't need to learn any of the frameworks here.
    
    The Flagging Website documentation is detailed, self-contained, and should cover the vast majority of use cases for the Flagging website from an administrative perspective, such as updating the predictive model and deploying the website to Heroku.

The code base is mainly built with the following frameworks; all of these but the last one are Python frameworks:

- Pandas (data manipulation framework, built on top of another framework called `numpy`.)
- Flask (web framework that handles routing of the website)
- Jinja2 (text markup framework that is used for adding programmatic logic to statically rendered HTML pages.)
- Click (CLI building framework)
- Postgresql

These frameworks may be intimidating if this is your first time seeing them and you want to make changes to the site. This page has some learning resources that can help you learn these frameworks.

## Flask & Jinja2

The [official Flask tutorial](https://flask.palletsprojects.com/en/1.1.x/tutorial/) is excellent and worth following if you want to learn both Flask and Jinja2.

???+ tip
    Our website's code base is organized somewhat similar to the code base built in the official Flask tutorial. If you are confused by how the code base is organized, going through the tutorial may help clarify some of our design choices. For more examples of larger Flask websites, check out the [flask-bones](https://github.com/cburmeister/flask-bones) template; we did not explicitly reference it in constructing our website but it nevertheless follows a lot of the same ideas we use.

## Pandas

The Pandas documentation has excellent resources for users who are coming from R, Stata, or SAS: [https://pandas.pydata.org/docs/getting_started/comparison/comparison_with_r.html](https://pandas.pydata.org/docs/getting_started/comparison/comparison_with_r.html)

## Click

Click is pretty easy to understand: it lets you wrap your Python functions with decorators to make the code run on the command line. We use Click to do a lot of our database management.

The [homepage for Click's documentation](https://click.palletsprojects.com/en/7.x/) should give you a good idea of what Click is all about. Additionally, Flask's documentation has a page [here](https://flask.palletsprojects.com/en/1.1.x/cli/) that discusses Flask's integration with Click.

## Postgresql

We do not do anything crazy with Postgresql. We made a deliberate decision to only use SQL for retrieving and storing data, and to avoid some of the more intermediate to advanced aspects of Postgres such as CTEs, views, and so on. Actual data manipulation is done in Pandas.

A simple [intro SQL tutorial](https://www.khanacademy.org/computing/computer-programming/sql) should be more than sufficient for understanding the SQL we use in this code base.
