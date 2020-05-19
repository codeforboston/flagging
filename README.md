# Flagging Website

This is the code base for the [Charles River Watershed Association's](https://crwa.org/) ("CRWA") flagging website. The flagging website hosts an interface for the CRWA's staff to monitor the outputs of a predictive model that determines whether it is reasonably safe to swim or boat in the Charles River.

This code base is built in Python 3.7+ and utilizes the Flask library heavily.

## For Developers

Please visit the [Flagging Website wiki](https://github.com/codeforboston/flagging/wiki) for on-boarding documents, code style guide, development updates, and more.

## Setup

These are the steps to set the code up in development mode.

**On Windows:** open up a Command Prompt terminal window (the default in PyCharm on Windows), point the terminal to the project directory if it's not already there, and enter:

```commandline
run_windows_dev
```

If you are in PowerShell (default VSC terminal), use `start-process run_windows_dev.bat` instead.

**On OSX or Linux:** open up a Bash terminal, and in the project directory enter:

```shell script
sh run_unix_dev.sh
```

After you run the script for your respective OS, it will ask you for a vault password. If you have the vault password, enter it here.
