# flagging_site Content 

  - `/blueprints`: custom endpoints for the flagging website (all the logic that helps to render the HTML pages or JSONs.)
  - `/data`: database, predictive models, and functions to retrieve live data.
  - `/static`: files that don't change, such as CSS files and images.
  - `/templates`: contains the html pages that define the web page structure.
  - `__init__.py`: required to treat this directory as a Python module.
  - `admin.py`: most of the admin panel stuff, and authorization for it.
  - `app.py`: main Flask application.
  - `config.py`: file holding the config options for flask and database.
  - `twitter.py`: Twitter bot message logic.
