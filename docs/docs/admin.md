# Admin Pages

You can reach all admin pages by going to /admin and inputting a username and password.
In development, the username is 'admin' and the password is 'password', but these should
be set as config variables `BASIC_AUTH_USERNAME` and `BASIC_AUTH_PASSWORD`. Remember to log out
by clicking the `Logout` button in the nav bar.

!!! tip foo bar

## Cyanobacteria Overrides

There should be a link to this page in the admin navigation bar.
On this page, one can add an override for a reach with a start time and end time,
and if the current time is between those times then the reach will be marked as
unsafe on the main website, regardless of the model data.
