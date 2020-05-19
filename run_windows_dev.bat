:: change `python` to `python3` or `python3.7` as you need to.
python -m venv venv
call venv\Scripts\activate.bat
python -m pip install -r requirements.txt

set FLASK_APP=flagging_site
set FLASK_ENV=development
set /p VAULT_PASSWORD="Enter vault password: "

flask run