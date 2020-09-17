:: change `python` to `python3` or `python3.7` as you need to.
python -m venv venv
call venv\Scripts\activate.bat
python -m pip install -r requirements.txt

set FLASK_APP=flagging_site:create_app
set FLASK_ENV=development
set /p OFFLINE_MODE="Offline mode? [y/n]: "

flask create-db
flask init-db
flask run
