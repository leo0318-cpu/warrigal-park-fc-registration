# Changelog

All notable changes to this project. Format loosely follows Keep a Changelog.
The project has not been released yet; versions track the milestone reached.

## [Unreleased] — Sprint 1

### Added
- **WBS 4.1 — Member CRUD** (`src/warrigal/member.py`, `src/warrigal/db.py`): create, find by
  partial family name, update, deactivate and reactivate, persisted in SQLite through the
  standard library so the $0 budget constraint holds with no third-party dependency. Search
  disambiguates by date of birth rather than by name; members are deactivated rather than
  deleted so registration history survives (D-06); validation names every failing field in a
  single message.
- **WBS 4.5 — Views** (`src/warrigal/views.py`): a team roster with contacts (a member under
  18 shows the linked guardian's number), a member's registration history across all seasons,
  and the juniors linked to a guardian. Each view discovers whether the tables owned by work
  packages 4.2–4.4 exist yet and, when one is missing, says so explicitly instead of guessing.
- Command line: `member add|find|show|update|deactivate|reactivate|roster-check` and
  `view roster|history|juniors`.
- 77 automated tests covering the US-01 to US-04 and US-11 to US-13 acceptance criteria.
- Jira product backlog: 2 epics, 13 user stories with acceptance criteria, 17 WBS tasks.
- Definition of Done (7 criteria) and the decision log (7 decisions).
- Risk register with 6 risks including the A2/A3 deadline exposure.
- `config.env.template` — the canonical list of settings the application understands.
- `deploy.sh` and `deploy.bat` — one command from a clean clone to a running application,
  supporting the clean-checkout verification in WBS 5.3.
- `config.env` added to `.gitignore`, so local values cannot be committed by accident.
- Team SCU email addresses recorded in the README for contribution attribution.

## [2026-09-22] — Planning phase complete (M2)

### Added
- Planning document set: Project Charter V1.0, kick-off meeting minutes, WBS and key milestones,
  project Gantt chart.
- Repository scaffold: README, contributing guide, pull-request and issue templates, CI workflow.
- Risk register and assumptions register.

### Fixed
- Gantt chart: `Phase` for the five development tasks (DEV1–DEV5) corrected from `Design` to
  `Development`; H1 (GitHub maintenance) dependency corrected from DEV1 to D3 so that it no
  longer starts before its predecessor finishes.

## [2026-09-20] — Kick-off (M1)

### Added
- Project Charter V1.0 approved by all four members.
- Kick-off meeting held; minutes and action items finalised.
