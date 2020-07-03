# Production Deployment

The following tools are required to deploy the website:

- [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli)
- [Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)

## Deploying for the first time

If you've never deployed the app from your computer, follow these instructions.

Note: the project name here is assumed to be `crwa-flagging`.

1. If you have not already done so, pull the repository to your computer, and then change your directory to it.

```shell
git clone https://github.com/codeforboston/flagging.git
cd ./flagging
```

2. Login to Heroku, and add Heroku as a remote repo using Heroku's CLI:

```shell
heroku login
heroku git:remote -a crwa-flagging
```

3. Add the vault password as an environment variable to Heroku.

```shell
heroku config:set VAULT_PASSWORD=replace_me_with_pw
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

```shell
2020-06-13T23:17:54.000000+00:00 app[api]: Build succeeded
```

If you see insted see something like `2020-06-13T23:17:54.000000+00:00 heroku[web.1]: State changed from starting to crashed`, then read the rest of the output to see what happened (there will likely be a lot of stuff, so dig through it). The most common error when deploying to production will be a `RuntimeError: Unable to load the vault; bad password provided` which is self-explanatory. Update the password, and the website will automatically attempt to redeploy. If you don't see that error, then try to self-diagnose.

7. Go see the website for yourself!

## Subsequent deployments

1. Heroku doesn't allow you to redeploy the website unless you create a new commit. Add some updates if you need to with `git add .` then `git commit -m "describe your changes here"`.

2. Once you have done that, Heroku will simply redeploy the site when you merge your working branch:

```shell
git push heroku master
```

## Staging and Production Split

It is recommended, though not required, that you have both "staging" and "production" environments for the website (see [here](https://en.wikipedia.org/wiki/Deployment_environment#Staging) for an explanation), and furthermore it is recommended you deploy to staging and play around with the website to see if it looks right before you deploy to prodution.

Managing effectively two separate Heroku apps from a single repository requires a bit of knowledge about how git works. Basically what you're doing is connecting to two separate remote git repositories. The default remote repo is called `heroku` and it was created by Heroku's CLI. But since you now have two Heroku remotes, the Heroku CLI doesn't know what it's supposed to name the 2nd one. So you have to manually name it using git.

1. Run the following command to create a staging environment if it does not already exist.

```shell
heroku create crwa-flagging-staging
```

2. Once it exists, add the staging environment as a remote; check to make sure all the remotes look right. The `heroku` remote should correspond with the production environment, and the `staging` remote should correspond with the staging environment you just created.

```shell
git remote add staging https://git.heroku.com/crwa-flagging-staging.git
git remote -v
```

3. Now all of your `heroku` commands are going to require specifying the app, but the steps to deploy in staging are otherwise similar to the production deployment:

```shell
heroku config:set --app crwa-flagging-staging VAULT_PASSWORD=replace_me_with_pw
git push staging master
heroku logs --app crwa-flagging-staging --tail
```

4. Check out the website and make sure it looks right.