# Deployment

???+ note
    This guide is an instruction manual on how to deploy the flagging website to internet via Heroku. If you just want to run the website locally, you do not need Heroku. Instead, check out the [development](/development) guide.

The following tools are required to deploy the website:

- [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli)
- [Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)

## First Time Deployment

???+ note
    In this section, the project name is assumed to be `crwa-flagging`. If you are deploying to another URL, such as `crwa-flagging-staging` or another personal domain, then replace each reference to `crwa-flagging` with that.

If you've never deployed the app from your computer, follow these instructions.

1. If you have not already done so, pull the repository to your computer, and then change your directory to it:

```shell
git clone https://github.com/codeforboston/flagging.git
cd ./flagging
```

  Additionally, make sure the `VAULT_PASSWORD` environment variable is set if it has not already been:
  
=== "Windows (CMD)"
    ```shell
    set VAULT_PASSWORD=replace_me_with_pw
    ```
=== "OSX (Bash)"
    ```shell
    export VAULT_PASSWORD=replace_me_with_pw
    ```

2. Login to Heroku, and add Heroku as a remote repo using Heroku's CLI:

```shell
heroku login
heroku git:remote -a crwa-flagging
```

3. Add the vault password as an environment variable to Heroku.

=== "Windows (CMD)"
    ```shell
    heroku config:set VAULT_PASSWORD=%VAULT_PASSWORD%
    ```
=== "OSX (Bash)"
    ```shell
    heroku config:set VAULT_PASSWORD=${VAULT_PASSWORD}
    ```

4. Now deploy the app!

```shell
git push heroku master
```

5. Now try the following:

```shell
heroku logs --tail
```

6. If everything worked out, you should see the following at or near the bottom of the log:

```
2020-06-13T23:17:54.000000+00:00 app[api]: Build succeeded
```

???+ note
    If you see instead see something like `[...] State changed from starting to crashed`, then read the rest of the output to see what happened. The most common error when deploying to production will be a `RuntimeError: Unable to load the vault; bad password provided` which is self-explanatory. Update the password, and the website will automatically attempt to redeploy. If you don't see that error, then try to self-diagnose.

7. Go see the website for yourself!

8. You are still not done; you need to do one more step, which is to set up the task scheduler.

## Subsequent Deployments

1. Heroku doesn't allow you to redeploy the website unless you create a new commit. Add some updates if you need to with `git add .` then `git commit -m "describe your changes here"`.

???+ note
    In the _very_ rare case you simply need to redeploy without making any changes to the site, in lieu of the above, simply do `git commit --allow-empty -m "redeploy"`.

2. Once you have done that, Heroku will redeploy the site when you merge your working branch:

```shell
git push heroku master
```

???+ tip
    If you are having any issues here related to merge conflicts, instead of deleting everything and starting over, try to pull the data from the `heroku` branch in and merge it into your local branch.
    
    ```shell
    git fetch heroku
    git pull heroku master
    ```

## Staging and Production Split

It is recommended, though not required, that you have both "staging" and "production" environments for the website (see [here](https://en.wikipedia.org/wiki/Deployment_environment#Staging) for an explanation), and furthermore it is recommended you deploy to staging and play around with the website to see if it looks right before you ever deploy to production.

Managing effectively two separate Heroku apps from a single repository requires a bit of knowledge about how git works. Basically what you're doing is connecting to two separate remote git repositories. The default remote repo is called `heroku` and it was created by Heroku's CLI. But since you now have two Heroku remote repositories, the Heroku CLI doesn't know what it's supposed to name the 2nd one. So you have to manually name it using git.

1. Run the following command to create a staging environment if it does not already exist.

```shell
heroku create crwa-flagging-staging
```

2. Once it exists, add the staging environment as a remote; check to make sure all the remotes look right. The `heroku` remote should correspond with the production environment, and the `staging` remote should correspond with the staging environment you just created.

```shell
git remote add staging https://git.heroku.com/crwa-flagging-staging.git
git remote -v
```

???+ success
    The above command should output something like this:
  
    ```shell
    heroku  https://git.heroku.com/crwa-flagging.git (fetch)
    heroku  https://git.heroku.com/crwa-flagging.git (push)
    origin  https://github.com/YOUR_USERNAME_HERE/flagging.git (fetch)
    origin  https://github.com/YOUR_USERNAME_HERE/flagging.git (push)
    staging https://git.heroku.com/crwa-flagging-staging.git (fetch)
    staging https://git.heroku.com/crwa-flagging-staging.git (push)
    upstream        https://github.com/codeforboston/flagging.git (fetch)
    upstream        https://github.com/codeforboston/flagging.git (push)
    ```

3. Now all of your `heroku` commands are going to require specifying the app, but the steps to deploy in staging are otherwise similar to the production deployment:


=== "Windows (CMD)"
    ```shell
    heroku config:set --app crwa-flagging-staging VAULT_PASSWORD=%VAULT_PASSWORD%
    git push staging master
    heroku logs --app crwa-flagging-staging --tail
    ```

=== "OSX (Bash)"
    ```shell
    heroku config:set --app crwa-flagging-staging VAULT_PASSWORD=${VAULT_PASSWORD}
    git push staging master
    heroku logs --app crwa-flagging-staging --tail
    ```

4. Check out the website in the staging environment and make sure it looks right.
