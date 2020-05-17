function get_python_exec() {
  # Get a Python executable that can run this app.
  pyver=`python3 -V | cut -b 8-`
  major=`echo ${pyver} | cut -d. -f1`
  minor=`echo ${pyver} | cut -d. -f2`
  # If python3 is 3.7+, then use that. Else, attempt to use "python3.7"
  if [ ${major} == 3 ] && [ ${minor} -ge 7 ]; then
    pyexec="python3"; else
    pyexec="python3.7"; fi
  echo ${pyexec}
}

# Get proper Python executable
PYEXEC=$(get_python_exec)

# Set up virtual environment in /venv
$PYEXEC -m venv venv
$PYEXEC -m pip install -r requirements.txt

# Set up and run the Flask application
export FLASK_APP=flagging_site
export FLASK_ENV=development
read -p "Enter vault password: " VAULT_PASSWORD
flask run