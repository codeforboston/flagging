# Documentation

The full docs are available at: https://codeforboston.github.io/flagging/

### Deploying / Refreshing the Docs

If you have write permission to the upstream repository (i.e. you are a project manager), point your terminal to this directory and run the following:

```shell script
python3 -m venv mkdocs_env
source mkdocs_env/bin/activate
pip install mkdocs pymdown-extensions mkdocs-material
mkdocs gh-deploy --remote-name upstream
deactivate
source ../venv/bin/activate
```

If you do not have write permission to the upstream repository, you can do one of the following:
 
 1. (Preferred) Ask a project manager to refresh the pages after you've made changes to the docs.
 2. Run `mkdocs gh-deploy` on your own fork, and then do a pull request to `codeforboston:gh-pages`:
 
```shell script
mkdocs gh-deploy
git checkout gh-pages
git push origin gh-pages
```
