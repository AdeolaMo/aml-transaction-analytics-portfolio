# Publish this repository on AdeolaMo GitHub

These instructions publish **this new synthetic demo only**. They do not make any Project Insight repositories public or copy their material.

## Option 1: GitHub CLI (easiest if installed/authenticated)

Extract the supplied ZIP and in a terminal run:

```bash
cd aml-transaction-analytics-portfolio
# First review this repository and confirm that all files are synthetic/demo.
git init -b main
git add .
git commit -m "Publish synthetic AML transaction analytics portfolio"
gh auth login # only if you have not previously authenticated
# Creates a NEW public repository from this folder.
gh repo create AdeolaMo/aml-transaction-analytics-portfolio --public --source=. --remote=origin --push
```

If the target repository name already exists, choose a different unused name. Publishing a new public portfolio repository is intentional: anyone can read its contents.

## Option 2: GitHub website + Git

1. Sign into `https://github.com/AdeolaMo`.
2. Select **New repository** and name it `aml-transaction-analytics-portfolio`, visibility **Public**. Do not initialize a README/license (they are included already).
3. Extract the ZIP, change into the project directory, then run:

```bash
git init -b main
git add .
git commit -m "Publish synthetic AML analytics portfolio"
git remote add origin https://github.com/AdeolaMo/aml-transaction-analytics-portfolio.git
git push -u origin main
```

The portfolio URL will be `https://github.com/AdeolaMo/aml-transaction-analytics-portfolio` **only after successful repository creation and push**.

## Optional interactive browser preview via GitHub Pages

The dashboard is in `dashboard/index.html`. To publish it using GitHub Pages without reorganising files, go to **Settings → Pages**, set source to **GitHub Actions**, or copy the standalone HTML into a `docs/index.html` file in the repo and deploy from `/docs` using the branch setting. Do not assume Pages is enabled until you verify the generated site.

## Before sharing

Verify the README displays the preview, download the Excel workbook, run the tests, and confirm your new repo URL loads in a browser while logged out. Be accurate about your own implementation role and AI-assisted development.
