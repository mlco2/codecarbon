# Contributing to CodeCarbon

New to open source? [Here's a guide to help you](https://opensource.guide/how-to-contribute/).
Want to talk to someone first? [Join us on Discord](https://discord.gg/GS9js2XkJR) — we're
happy to help you find something to work on.

## Where to start

- **Have a question?** Check the [FAQ](https://docs.codecarbon.io/latest/explanation/faq/),
  then ask on [Discord](https://discord.gg/GS9js2XkJR).
- **Found a bug?** [Open an issue](https://github.com/mlco2/codecarbon/issues/new), and feel
  free to send a pull request with the fix too.
- **Have a feature request?**
  [Open an issue](https://github.com/mlco2/codecarbon/issues/new) describing the feature and
  its intent. Please search the existing issues first to avoid duplicates.
- **Want to write code?** Look for
  [good first issues](https://github.com/mlco2/codecarbon/labels/good%20first%20issue) and
  [help wanted](https://github.com/mlco2/codecarbon/labels/help%20wanted), or pick something
  from the [prioritized board](https://github.com/orgs/mlco2/projects/1).
- **Your CPU isn't recognised?** Adding it to `codecarbon/data/hardware/cpu_power.csv` is a
  genuinely useful first contribution: it improves accuracy for everyone with that hardware.
- **Documentation unclear?** Every docs page has an edit button.

## Set up your environment

CodeCarbon is a Python package. We use [UV](https://github.com/astral-sh/uv) to manage
environments, Python versions and dependencies — install it with the
[standalone installer](https://docs.astral.sh/uv/getting-started/installation/#standalone-installer),
then:

```sh
git clone https://github.com/mlco2/codecarbon.git
cd codecarbon
uv sync
uv run task pre-commit-install
```

## Run the tests

```sh
uv run task test-package
```

Most pull requests are expected to contain either new tests or test updates. See
[development](development.md#tests) for details.

## Check style before you push

```sh
uv run task format
```

The pre-commit hook runs these for you.

## Open your pull request

`master` is protected, so branch from it and open a pull request — draft pull requests are
welcome if you want early feedback. Keep the change focused and describe the problem it
solves; documenting the intent and the limits of a contribution, in the pull request or in a
dedicated issue, helps the review. Once the automated tests pass, a maintainer reviews and
merges it.

## Alternative ways of contributing

You have a cool idea, but do not know if it fits with CodeCarbon? You can create an issue to
share:

-   the code, via the GitHub repo or [Binder](https://mybinder.org/), to share executable notebooks
-   a webapp, using [Voilà](https://github.com/voila-dashboards/voila), [Dash](https://github.com/plotly/dash) or [Streamlit](https://github.com/streamlit/streamlit)
-   ideas for improvement about the tool or its documentation

## More detail

- [Development guide](development.md) — UV commands, debugging, stress testing, dependency
  management, building the docs, running the API and dashboards locally
- [Maintainer guide](../maintaining.md) — release process and deployment
- [AI policy](ai_policy.md)
- [Code of conduct](code-of-conduct.md)

## Questions or Need Help?

Got stuck? Have an idea? Want to share your contribution?
**[Join us on Discord](https://discord.gg/GS9js2XkJR)** – our community is here to help and
support you!

## License

By contributing your code, you agree to license your contribution under the terms of the
[MIT License](https://github.com/mlco2/codecarbon/blob/master/LICENSE).

All files are released with the MIT license.
