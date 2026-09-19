# Warrigal Park FC — Member Registration & Team Roster System

A single authoritative register of club members, their guardians, season registrations and
team rosters — replacing the paper forms, the 43-column Excel master spreadsheet and the
second data-entry pass into PlayRegister.

| | |
| --- | --- |
| **Unit** | ISY3001 2026-T4 Managing Software Development |
| **Assessment** | Assignment 3 (Group, 50%) — due Monday 19 October 2026, 23:49 AEDT (GXUST cohort) |
| **Team** | MSD426-GXUST25 |
| **Case study** | case-study-6 — Warrigal Park Football Club |
| **Client** | Warrigal Park Football Club Inc., 60 Kluver Street, Bald Hills, Brisbane |
| **Status** | Planning phase complete — Sprint 1 in progress |
| **Documentation** | Confluence space: `<paste the space URL>` |
| **Backlog** | Jira project: `<paste the project URL>` |

---

## The problem

Warrigal Park FC registers players on paper, transcribes the forms into a 43-column Excel
master spreadsheet, types the same details a second time into the association's PlayRegister
system, and then distributes age-group lists by hand. The same data is entered three times,
siblings are entered as separate families, players who share a name are confused, and in 2024
a player took the field whose registration had not gone through — an insurance-liability risk
(association circular, item 4).

## What this iteration delivers

| Capability | Description |
| --- | --- |
| Member | Create, find, update and deactivate members |
| Guardian | Create, find and update guardians; link one guardian to one or more juniors |
| Registration | Register a player for a season with a status flow (Started / Complete / Withdrawn) |
| Team & Roster | Create a team for a season; place, move and remove players |
| Views | Team roster with contacts; a member's registration history; a guardian's juniors |

**The one rule that must never break:** a player under 18 cannot complete a registration
without a linked guardian (risk R1, story US-08, WBS 3.2 / 4.3 / 5.1).

## Out of scope this iteration

Fees and finance, PlayRegister integration, compliance checks (Blue Card / Working with
Children), squad and age validation, fixtures/results/ladders, canteen roster, uniforms and
merchandise. These sit in the product backlog and are deliberately not built.

## Constraints

- **$0 budget** — free tooling only; the application itself uses the Python standard library.
- Runs as a **Python command-line application**.
- Delivered so that a **clean checkout runs from the README alone**.
- Minors' privacy is protected — no personal data is stored that the club does not need.

---

## Repository layout

```
warrigal-park-fc-registration/
├─ src/warrigal/            Application package (implementation lands in Sprints 1–2)
├─ tests/                   Automated tests (WBS 5.1–5.3)
├─ docs/                    Planning documents (WBS 1.1–1.3)
│  └─ original/             The four signed-off planning documents
├─ .github/                 Pull-request and issue templates, CI workflow
├─ CONTRIBUTING.md          Branch strategy, commit convention, review rules
├─ pyproject.toml           Package metadata and pytest configuration
└─ CHANGELOG.md             What changed and when
```

## Getting started

### Prerequisites

- Python 3.11 or newer (`python --version`)
- Git

### Clean checkout

```bash
git clone <repository-url>
cd warrigal-park-fc-registration
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt  # dev/test tooling only — no runtime dependencies
pip install -e .                 # makes `python -m warrigal` resolve from the source tree
python -m warrigal --help
```

Run the test suite:

```bash
python -m pytest -q
```

> **Definition of Done, criterion 5:** this must work from a fresh clone on a machine that has
> never seen the project. If it does not, the story is not done.

## Development workflow

1. Pick up a story in Jira and move it to **In Progress**.
2. Branch: `feature/4.1-member-crud` (see `CONTRIBUTING.md`).
3. Commit using the convention `feat(4.1): add member search by family name`, and put the Jira
   key in the commit body.
4. Open a pull request against `main` using the repository template; request a review from at
   least one other member.
5. Squash-merge once reviewed and the CI workflow is green.

## Definition of Done

A story is done when every acceptance criterion is demonstrated and recorded on the Jira issue,
the pull request was reviewed and approved, automated tests cover the change, the under-18
guardian rule test still passes, the app runs from a clean checkout, and the README and
decision log are updated. Full detail: `docs/07-definition-of-done.md`.

## Work breakdown (WBS)

| Phase | Work packages | Owner |
| --- | --- | --- |
| 1.0 Project Management | 1.1–1.3 | Cao Yang |
| 2.0 Requirements & Backlog | 2.1–2.3 | Chen Shuai |
| 3.0 System Design | 3.1–3.3 | Zhang Runze |
| 4.0 Development | 4.1–4.5 | Zhang Runze (with Chen Shuai, Zhou Kunpeng) |
| 5.0 Testing | 5.1–5.3 | Zhang Runze |
| 6.0 Delivery Preparation | 6.1–6.3 | Cao Yang |
| 7.0 Project Closure | 7.1–7.2 | Cao Yang |

## Team

| Name | Role | SCU email |
| --- | --- | --- |
| Cao Yang | Project Manager | _to be added_ |
| Chen Shuai | Business / Requirements Lead + Scribe | _to be added_ |
| Zhang Runze | Technical Lead | _to be added_ |
| Zhou Kunpeng | Scheduling Lead | k.zhou.14@student.scu.edu.au |

> Add each member's SCU email here and in Jira before the first pull request, so that GitHub and
> Jira attribute contributions to the right person.

## Milestones

| ID | Milestone | Date |
| --- | --- | --- |
| M1 | Project kick-off complete | 2026-09-20 |
| M2 | Planning documents approved | 2026-09-22 |
| M3 | Requirements approved (sprint backlog set) | 2026-09-27 |
| M4 | Design approved | 2026-09-30 |
| M5 | Development complete | 2026-10-09 |
| M6 | Testing complete (DoD met) | 2026-10-12 |
| M7 | Delivery preparation complete | 2026-10-13 → 14 |
| M8 | Project closure | 2026-10-15 |

## Documentation index

| Document | Location |
| --- | --- |
| Project Charter | `docs/01-project-charter.md` |
| Team Meeting Minutes | `docs/02-team-meeting-minutes.md` |
| WBS and Key Milestones | `docs/03-wbs-and-key-milestones.md` |
| Gantt Chart | `docs/04-gantt-chart.md` + `docs/original/04_Project_Gantt_Chart.xlsx` |
| Risk Register | `docs/05-risk-register.md` |
| Decision Log | `docs/06-decision-log.md` |
| Definition of Done | `docs/07-definition-of-done.md` |
| Progress Report | `docs/08-progress-report-2026-09-22.md` |

The Confluence space is the single source of truth for decisions and assumptions; the copies
in `docs/` are the snapshots submitted with the assignment.
