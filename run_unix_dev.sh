function get_python_exec() {
  # Get a Python executable that can run this app.
  for pyexec in "python" "python3" "python3.7" "python3.8" "python3.9"
  do
    pyver=`${pyexec} -V | cut -b 8-`
    major=`echo ${pyver} | cut -d. -f1`
    minor=`echo ${pyver} | cut -d. -f2`
    # If python3 is 3.7+, then use that.
    # Otherwise, continue the loop.
    if [ ${major} == 3 ] && [ ${minor} -ge 7 ]; then
      echo ${pyexec}
      break
    fi
  done
}

# Get proper Python executable
PYEXEC=$(get_python_exec)

# Set up virtual environment in /venv
$PYEXEC -m venv venv
source venv/bin/activate
$PYEXEC -m pip install -r requirements.txt

# Set up and run the Flask application
export FLASK_APP=flagging_site
export FLASK_ENV=development
read -p "Offline mode? [y/n]: " offline_mode
export OFFLINE_MODE=${offline_mode}
read -p "Enter vault password: " vault_pw
export VAULT_PASSWORD=${vault_pw}
flask run