:: change `python` to `python3` or `python3.7` as you need to.
python -m venv venv
call venv\Scripts\activate.bat
python -m pip install -r requirements/dev_windows.txt

set FLASK_APP=app:create_app
set FLASK_ENV=development
set /p USE_MOCK_DATA="Use mock data? [y/n]: "

flask create-db
flask init-db
flask clear-cache
flask run
