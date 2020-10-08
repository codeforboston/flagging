# Website Administration

## Admin Panel

???+ Note
    This section discusses how to use the admin panel for the website. For how to set up the admin page username and password during deployment, see the [Heroku deployment](cloud/heroku_deployment) documentation.

The admin panel is used to manually override the model outputs during events and advisories that would adversely effect the river quality.

You can reach the admin panel by going to `/admin` after the base URL for the flagging website. (You need to it in manually.)

You will be asked a username and password, which will be provided to you by the person who deployed the website. Enter the correct credentials to enter the admin panel.

???+ note
    In "development" mode, the default username is `admin` and the password is `password`. In production, the environment variables `BASIC_AUTH_USERNAME` and `BASIC_AUTH_PASSWORD` are used to set the credentials.

### Cyanobacteria Overrides

There should be a link to this page in the admin navigation bar.
On this page, one can add an override for a reach with a start time and end time,
and if the current time is between those times then the reach will be marked as
unsafe on the main website, regardless of the model data.

## Update Database Manually

Going to `/admin/update-db` will update the database manually. (If you have not yet been authenticated, you will be asked to enter your credentials.)

Be patient, as updating the database will take a few moments. If the database updates succesfully, you will see a message indicating that the update worked, and you will be redirected to the home page.
