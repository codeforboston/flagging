# Documentation

The full docs are available at: https://codeforboston.github.io/flagging/

### Deploying / Refreshing the Docs

If you have write permission to the upstream repository (i.e. you are a project manager), point your terminal to this directory and run the following:

```shell script
mkdocs gh-deploy --remote-branch upstream
```

If you do not have write permission to the upstream repository, you can do one of the following:
 
 1. (Preferred) Ask a project manager to refresh the pages after you've made changes to the docs.
 2. Run `mkdocs gh-deploy` on your own fork, and then do a pull request to `codeforboston:gh-pages`
 
 If you are a project manager but you're having issues, you can do a more manual git approach to updating the docs:
 
```shell script
mkdocs gh-deploy
git checkout gh-pages
git push upstream gh-pages
```