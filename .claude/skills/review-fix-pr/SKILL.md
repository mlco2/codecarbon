---
name: review-fix-pr
description: Use when asked to review a codecarbon pull request or branch and fix what the review finds, check its coverage like CI, or prepare a PR description to paste on GitHub.
---

# Review, fix and describe a codecarbon PR

Read the PR description on Github, read the linked issues, and read the comments.

Three deliverables: a list of review findings, one commit per fixed finding (each with a test that fails without it), and an uncommitted `PR_review_message.md` to paste on GitHub.

## 1. Review

- Run the `code-review` skill on the PR number (or the branch). Rank findings most severe first.
- Show the findings to the user before fixing them, unless they already asked for the fixes.

## 2. Check coverage like CI

CI runs `uv run task test-coverage` and Codecov checks **patch** coverage (the changed lines only):

```bash
S=<scratchpad>; mkdir -p $S/home
HOME=$S/home UV_CACHE_DIR=~/.cache/uv uv run task test-coverage   # clean HOME, as in CI
git diff -U0 master...HEAD -- codecarbon/ > $S/diff.patch
uv run python -I .claude/skills/review-fix-pr/scripts/patch_coverage.py $S/diff.patch coverage.xml
```

`HOME` must point to an empty directory: a `~/.codecarbon.config` makes 7 tests in `test_config.py` and `test_electricitymaps_config_backward_compatibility.py` fail locally, though they pass in CI. Cover every missed line with a test.

## 3. Fix, one commit per finding

For each finding:

1. Write the test, then the fix.
2. Prove the test catches the bug: `git stash -q -- codecarbon; uv run pytest -q <test> ; git stash pop -q` must show it failing.
3. Commit with the format hooks run first. Otherwise black rewrites files and the commit aborts:

```bash
git add -u; uv run pre-commit run >/dev/null 2>&1; git add -u
git commit -m "fix(<area>): <what>" -m "<why, the failure scenario>" -m "Co-Authored-By: ..."
```

Order commits so each builds on the previous one (refactors that others rely on go first). Update `docs/` in the commit that changes the documented behaviour.

When finished, re-run step 2: expect 0 failures and 100 % patch coverage.

## 4. PR_message.md

Write it at the repo root and add it to `.git/info/exclude` so it is never committed. Start from the PR's current body (`gh pr view <n> --json title,body`) and keep the template in `.github/PULL_REQUEST_TEMPLATE.md`. It contains:

- **Description** of the whole PR as it now behaves, not only the review fixes.
- **Changes after review**: a table with each commit title and the bug it fixes.
- **Behaviour changes** a reviewer must know about.
- **How Has This Been Tested?**: test counts and patch coverage from step 2.
- Updated checklist (docs boxes included).

## Common mistakes

| Mistake | Instead |
| --- | --- |
| Comparing with master using `git checkout master -- .` | `git worktree add <scratchpad>/wt master`; remove it afterwards |
| Treating failures that only appear when some test files run together as regressions | Re-run the same files in a master worktree. A test that swaps modules in `sys.modules` must restore them (see `IsolatedGPUModules` in `tests/test_gpu_nvidia.py`) |
| A test that passes with and without the fix | Check step 3.2 for every test |
| `pytest.approx(x)` on energies with a 1000 mJ baseline | `rel=1e-5` |
| Counting warnings on all GPUs (fakes have 2) | Filter messages on `GPU 0` |
