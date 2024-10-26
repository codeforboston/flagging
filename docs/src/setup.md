# Setup

This is a guide on how to do your first-time setup for running the website locally and getting ready to make changes to the code base. If you are a developer, you should follow this guide before doing anything else!

This guide assumes you're a complete beginner at Python, Git, Postgres, etc. so don't be intimidated if you don't know what all of these things are. The main thing this guide assumes is that you know how to open up a terminal in your respective operating system (command prompt or Powershell in Windows, and bash/zsh in OSX).

**We strongly recommend running this project via Docker Compose.** You can attempt to run the project without Docker Compose, but instructions are not included.

**We also strongly recommend using `uv` for Python binary + dependency management.**

## Dependencies

Install all of the following programs onto your computer:

**Required:**

- [uv](https://docs.astral.sh/uv/#getting-started)
- [Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) (first time setup guide [here](https://git-scm.com/book/en/v2/Getting-Started-First-Time-Git-Setup))
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)

**Recommended:**

- A good text editor or IDE, such as [PyCharm](https://www.jetbrains.com/pycharm/) (which is powerful but bulky and geared toward advanced users).
- [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli) _(required for remote deployment to Heroku.)_

**Other:**

- It is strongly recommend that you create a [GitHub account](https://github.com/) if you haven't done so already. The GitHub account should have the same email as the one registered to your `git config --global user.email` that you set in the first time git setup.

## Download and Setup the Code Base

The flagging website is open source; the whole website's source code is available on GitHub. This section of the setup guide shows you the preferred way to install it and set up the code on a local computer.

1. Fork the [main GitHub repo](https://github.com/codeforboston/flagging/) to your personal GitHub account. You can do that by going to the Code For Boston flagging repo and clicking on this button:

![](img/github_fork.png)

2. Point your terminal (Bash on OSX, command prompt on Windows) to the directory you want to put the `/flagging` project folder inside of. E.g. if you want the project folder to be located at `<yourname>/Documents/flagging`, then point your directory to `<yourname>/Documents`. You can change directories using the `cd` command: `cd "path/goes/here"`

3. Run the following to download your fork and setup the connection to the upstream remote. Replace `YOUR_USERNAME_HERE` (in the first line) with your actual GitHub username.

```shell
git clone https://github.com/YOUR_USERNAME_HERE/flagging/
cd flagging
git remote add upstream https://github.com/codeforboston/flagging.git
git fetch upstream
```

4. In your newly created `flagging` folder, run the following:

```shell
cp -n .env.example .env
```

???+ danger
    If you do any commits to the repo, _please make sure `.env` is properly gitignored!_ (`.env.example` does not need to be gitignored, only `.env`.) `.env` contains sensitive information.

5. The previous step created a file called `.env` (pronounced "dot env"). This file will contain our HOBOlink credentials and Twitter/X credentials.

    Please update `.env` (**_NOT_** `.env.example`) to contain the correct credentials by replacing each `replace_me`. The Twitter/X credentials are optional.

    If you do not have HOBOlink credentials, please turn on demo mode by setting `FLASK_ENV=demo`.

## Run the Website Locally

After you get everything set up, you should run the website at least once.

1. Although not strictly required for running the website (as we will be using Docker Compose), it is recommended you install all the project dependencies into a virtual environment.

    To do this, run the following:

    ```
    uv pip sync requirements.txt
    ```


=== "Windows (CMD)"
    ```shell
    run_windows_dev
    ```

=== "OSX (Bash)"
    ```shell
    sh run_unix_dev.sh
    ```

???+ note
    The script being run is doing the following, in order:

    1. Set up a "virtual environment" (basically an isolated folder inside your project directory that we install the Python packages into),
    2. install the packages inside of `requirements/dev.txt`; this can take a while during your first time.
    3. Set up some environment variables that Flask needs.
    4. Prompts the user to set some options for the deployment. (See step 2 below.)
    5. Set up the Postgres database and update it with data.
    6. Run the actual website.

???+ tip
    If you are receiving any errors related to the Postgres database and you are certain that Postgres is running on your computer, you can modify the `POSTGRES_USER` and `POSTGRES_PASSWORD` environment variables to connect to your local Postgres instance properly.

    You can also save these Postgres environment variables inside of your `.env` file, but **do not** save your system password (the password you use to login to your computer) in a plain text file. If you need to save a `POSTGRES_PASSWORD` in `.env`, make sure it's a unique password, e.g. an admin user `POSTGRES_USER=flagging` and a password you randomly generated for that user `POSTGRES_PASSWORD=my_random_password_here`.

2. You will be prompted asking if you want to run the website with mock data. The `USE_MOCK_DATA` variable is a way to run the website with dummy data without accessing the credentials. It is useful for anyone who wants to run a demo of the website regardless of their affiliation with the CRWA or this project. It has also been useful for development purposes in the past for us.

3. Now just wait for the database to start filling in and for the website to eventually run.

???+ success
    You should be good if you eventually see something like the following in your terminal:

    ```
     * Serving Flask app "app:create_app" (lazy loading)
     * Environment: development
     * Debug mode: on
     * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
     * Restarting with stat
    ```

???+ error
    If you get an error that says something like "`Microsoft Visual C++ 14.0 or greater is required.`," you need to follow the link provided by the error message, download and install it, then reboot your computer.

4. Point your browser of choice to the URL shown in the terminal output. If everything worked out, the website should be running on your local computer!

![](img/successful_run.png)
