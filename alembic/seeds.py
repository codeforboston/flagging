# This file should contain records you want created when you run flask db seed.


initial_user = {
    'username': 'superadmin'
}
if User.find_by_username(initial_user['username']) is None:
    User(**initial_user).save()
