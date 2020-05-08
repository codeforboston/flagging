pip install -r requirements.txt
set FLASK_APP=flagging_site
set FLASK_ENV=development
set /p VAULT_PASSWORD="Enter vault password: "
flask run