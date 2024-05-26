# Documentation

The full docs are available at: https://codeforboston.github.io/flagging/

### Info

The docs were made with [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/).

There are a lot of extensions included in this documentation in addition to Material:

- Most of the extensions come from [PyMdown Extensions](https://facelessuser.github.io/pymdown-extensions/).
- We use a tool called [Mermaid](https://mermaid-js.github.io/mermaid-live-editor/) for our flow charts.
- We use the [macros plugin](https://squidfunk.github.io/mkdocs-material/reference/variables/) but only to parameterize the flagging website URL (the `flagging_website_url` field inside of `mkdocs.yml`).

All of these tools are added and configured inside `mkdocs.yml`. Note you need to pip install them for them to work when you deploy; see deployment script below.

Docs are deployed automatically via Github Actions after every merge to the main branch.
