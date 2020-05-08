pip install -r requirements.txt
export FLASK_APP=flagging_site
export FLASK_ENV=development
read -p "Enter vault password: " VAULT_PASSWORD
flask run