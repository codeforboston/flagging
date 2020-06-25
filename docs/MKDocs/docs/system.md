# Website Explained 

## Diagram
![Image of Yaktocat](Flaggin_System.png)

## Explanation

Here is a tentative explanantion of how the website works. Currently it is a flask web application  that creates a main web application using `create_app()` function and retrieve configuration options from `config.py` and keys from the `vault.zip`. Then joins mini web apps by registering blueprints found inside the `blueprints` directory. Particularly the main web app will be joining web app `flagging.py` to retrieve data from USGS and Hobolink api. With this information, we generate predictive data based on multiple logistic models to determine if river is safe or not. The website displays that data calling `render_template()` which renders `output_model.html` with the Jinja template engine. Moreover, we save that data inside a SQL database hosted in heroku, which will also where we deploy the flask web application.
