# Flagging Website

This is the code base for the [Charles River Watershed Association's](https://crwa.org/) ("CRWA") flagging website. The flagging website hosts an interface for the CRWA's staff to monitor the outputs of a predictive model that determines whether it is reasonably safe to swim or boat in the Charles River.

This code base is built in Python and utilizes the Flask library heavily.

## For Developers

Please visit the [Flagging Website wiki](https://github.com/codeforboston/flagging/wiki) for on-boarding documents, code style guide, development updates, and more.

Note: I _strongly_ recommend using a full-featured IDE for work on this project, as you'll likely want to have multiple terminals and `py` files open simultaneously. [PyCharm](https://www.jetbrains.com/pycharm/) and [Visual Studio Code](https://code.visualstudio.com/) are two very good IDEs that work well with this workflow.

## Setup

These are the steps to set the code up in development mode.

**On Windows:** open up a command prompt terminal window, and in the project directory enter:

```commandline
run_windows_dev
```

**On OSX or Linux:** open up a terminal, and in the project directory enter:

```bash
sh run_unix_dev.sh
```

After you run that script, it will ask you for a vault password. If you have the vault password, enter it here.
