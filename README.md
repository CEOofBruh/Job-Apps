# Job agent (GitHub Pages edition)

A free, hosted dashboard that collects remote web-design and WordPress postings,
scores them against your resume with Claude, and drafts cover letters.
You approve each one and submit it yourself.

## How it fits together

- `.github/workflows/fetch-jobs.yml` runs daily at 06:00 Philippine time (and on demand).
  It runs `scripts/fetch_jobs.py`, which reads `config.json` and writes `docs/jobs.json`.
- `docs/` is the website GitHub Pages serves. It loads `jobs.json`, and calls Claude from
  your browser using your own API key to score jobs and write letters.
- Scores, letters, and statuses are stored in your browser (Settings has export/import).

## Launch

1. Create a GitHub repo and push everything in this folder to the `main` branch.
2. Repo Settings > Pages > Build and deployment: Deploy from a branch > `main` / `/docs`.
3. Repo Settings > Actions > General > Workflow permissions: choose "Read and write permissions".
4. Actions tab > "Fetch jobs" > Run workflow. Check the log for source errors.
5. Open `https://<your-username>.github.io/<repo-name>/`, then Settings > paste your Anthropic API key.
6. Reload jobs > Score new jobs > review > Draft > Approve > Open application.

## Free mode (no API key)

Skip the key entirely. "Score new jobs" and "Draft cover letter" then open a window with a
ready-made prompt. Copy it into a Claude chat, paste Claude's reply back, and choose "Import reply".
Scoring works on 10 jobs per prompt. Adding an API key in Settings later makes both steps automatic.

## Tuning the search

Edit `config.json` on GitHub:

- `target_titles`: a posting's title must contain one of these.
- `exclude_keywords`, `exclude_locations`: skip matches.
- `locations`: keep postings whose location contains one of these (or has no location).
- `sources`: Greenhouse/Lever/Ashby company boards plus Remotive and RemoteOK.
  The token is the company's slug in its job-board URL, for example
  `boards.greenhouse.io/<token>`, `jobs.lever.co/<token>`, `jobs.ashbyhq.com/<token>`.
  Boards that fail to load appear in red at the top of the dashboard.

## Privacy

GitHub Pages sites are public, and so is everything in `docs/`, including
`docs/profile.default.json` (your resume details; email and phone are left out).
Your API key and your progress are never in the repo; they live only in your browser.
