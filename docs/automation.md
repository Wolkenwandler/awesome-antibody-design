**English** · [中文](automation.zh-CN.md)

# Literature tracking guide

This repository tracks AI protein design and antibody engineering. The README presents papers in eight research sections; topic pages use the same catalog. English is the default. Use the **中文** link at the top of any page to open its Chinese counterpart. Paper titles and author names remain in their original language.

## Enable automation

1. Push the implementation to the default branch.
2. In **Settings → Actions → General → Workflow permissions**, enable **Allow GitHub Actions to create and approve pull requests**. Organization policy may require an administrator.
3. Open **Actions → Update literature → Run workflow**. Start with a two-day window.
4. Check the run summary, `retrieval-report` artifact and `codex/literature-update` PR.

The workflow runs daily at 01:23 UTC, looking back 14 days, or 60 days on Sundays. Manual input accepts 1–90 days. GitHub schedules may be delayed or disabled after extended inactivity in public repositories. The workflow uses GITHUB_TOKEN, creates review PRs and does not approve or merge them. No paid model or personal access token is required.

Runs are serialized, with a 45-minute timeout, 200 pages per source and up to three attempts per request. Default-token PR creation generally does not trigger other PR workflows; do not rely on that behavior for required checks.

## Review and maintain papers

- Edit `data/papers.json`, not generated README sections or `papers/` pages.
- New entries have status `candidate`. After reviewing relevance, change to `curated` and correct `topic` and `tags`.
- Set unwanted entries to `excluded`, or add `{"id": "paper ID", "reason": "reason"}` to `data/exclusions.json` before removing the entry.
- Merging a catalog PR does not automatically mark its candidates as curated.
- Edit homepage introductions in `config/readme-header.md` and `config/readme-header.zh-CN.md`.
- Run the renderer to update both languages together. They share paper IDs, links, tags and review decisions.
- Resource links come from existing records or explicit source metadata. The collectors do not guess code URLs or generate scientific conclusions.

## Search and coverage

`config/topics.json` configures object terms, method terms and ordered category rules using only the Python standard library. Both term groups must match. Classification checks the title before the abstract. Unclassified relevant candidates fall back to `generation` and require review.

Europe PMC uses first-indexed dates; bioRxiv uses date ranges followed by local filtering; arXiv uses submission dates. Revisions of older arXiv papers and publication relationships discovered outside the lookback window may be missed. This is not a complete historical revision monitor. Evidence is limited to metadata/abstracts unless explicitly reviewed.

Deduplication uses DOI, arXiv ID, PMID, source links and exactly matching normalized titles. Explicit bioRxiv publication DOI relationships connect versions. Different titles without a confirmed relationship may remain separate; fuzzy titles are not automatically merged. Ambiguous matches are reported for review.

`first_seen` records discovery dates and is empty for imported records; `published` is the source-reported date. `observations` retains source/version metadata. Run artifacts retain retrieval windows and source status without creating daily no-op catalog changes.

A failed or over-budget source contributes no partial results. Successful sources may still produce a PR, while the workflow ends in failure with an error report. Existing records are retained. Narrow the date interval when a pagination budget is exceeded.

## Commands

Python 3.9+, standard library only. Follow the project's execution-environment rules.

```bash
# Generate both languages offline
python3 scripts/render_papers.py
# Offline verification in an authorized environment
python3 -m unittest discover -s tests -v
# Network collection in Actions or an approved environment
python3 scripts/update_papers.py --days 14
python3 scripts/update_papers.py --start 2026-09-01 --end 2026-09-07
```

`scripts/migrate_readme.py` is a one-time importer for the old README format. It must not import today's generated pages and refuses to overwrite an existing catalog. Original imported entries are retained in the data for provenance; importing is not a fresh metadata verification.

## Validation boundary

Local offline migration, rendering and unit tests were authorized for this implementation. Live API behavior, repository permissions and remote PR creation require verification in GitHub Actions. No scientific experiment is involved.

References: [GitHub scheduling](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows), [create-pull-request](https://github.com/peter-evans/create-pull-request), [Europe PMC](https://europepmc.org/RestfulWebService), [bioRxiv](https://api.biorxiv.org/), [arXiv](https://info.arxiv.org/help/api/user-manual.html).

## Historical backfill

Use the workflow's `backfill_start` and optional `backfill_end` inputs for a one-time historical update. Retrieval runs in contiguous calendar-month windows, with at most 24 batches, a 110-minute retrieval budget and a 120-minute job limit. Each batch is capped at 30 minutes. The first failed batch stops the sequence and preserves successful data and per-window reports in the artifact. Resume from the failed window after diagnosis; do not claim full coverage from an incomplete run.

Retrieval now uses explicit protein-design/modeling phrases and title context to reduce unrelated clinical results. Existing unreviewed candidates are re-filtered; human-curated entries are preserved. This remains a discovery filter, not a substitute for scientific review.

Historical bioRxiv discovery uses Europe PMC's official preprint index (`SRC:PPR AND PUBLISHER:"bioRxiv"`) with `FIRST_PDATE`, rather than scanning every bioRxiv post across all disciplines. Records explicitly identify the index source; historical revision lists are not exhaustively fetched. Daily incremental runs still query bioRxiv directly. arXiv uses a compact object/date query followed by local relevance screening.

On the current hosted runner, even minimal arXiv requests return HTTP 406 (diagnostic run 35506844401). Historical mode therefore uses Europe PMC's **partial arXiv preprint index** as a separate, explicitly labeled source. Successful completion means all requested index windows were processed; it does not certify exhaustive arXiv coverage. The direct arXiv limitation remains recorded rather than being treated as an empty direct result.
