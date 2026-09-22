## 9. Progress Report — Planning Phase

# 08 Progress Report — Planning Phase (as at 22 September 2026)

## Where we are

| Stage | Status | Evidence |
| --- | --- | --- |
| Project initiation and approval | **Complete** | Project Charter V1.0 signed by all four members; kick-off minutes finalised |
| Project planning (WBS + Gantt) | **In progress — ~90%** | WBS (7 phases, 22 work packages), eight milestones and the Gantt chart drafted and cross-reviewed |
| Project execution (SCRUM) | **Starting this week** | Product backlog built in Jira; Sprint 1 to be committed at M3 (27 Sep) |
| Software procurement (RFP) | Not started | Input to Assessment 2 |
| Project closure | Not started | Planned 14–15 October |

## What has been completed

1. **Team and roles** — four roles assigned: PM, Business/Requirements Lead + Scribe, Technical Lead, Scheduling Lead.
2. **Project Charter V1.0** — background, six measurable success criteria, scope and out-of-scope lists, $0 budget and constraints, four stakeholder groups, feasibility conclusions, five risks, milestone overview.
3. **Kick-off meeting minutes** — six agenda items, five action items, four open issues, communication plan.
4. **WBS and key milestones** — seven phases, 22 work packages under the 8/80 rule, eight milestones M1–M8.
5. **Project Gantt chart** — 24 tasks (P1–C2) with dependencies plus the eight milestones, weekdays only.
6. **Definition of Done and Decision Log** — seven criteria and seven recorded decisions.
7. **Jira product backlog** — 2 epics, 13 user stories with acceptance criteria and story-point estimates, 17 WBS tasks; Sprint 1 scope provisionally set at 7 stories (27 points).
8. **GitHub repository** — repository structure, README, contributing guide, PR and issue templates, and the four planning documents committed.

## Metrics

| Metric | Value |
| --- | --- |
| Milestones achieved / planned to date | M1 achieved (1 of 1 due) |
| Planning documents complete | 4 of 4 |
| Product backlog size | 13 user stories, 51 story points |
| Committed stories (8–15 target) | 13 — within target |
| Sprint 1 provisional scope | 7 stories, 27 story points |
| Open risks | 6 (R6 raised this week) |
| Open issues from kick-off | 3 of 4 |

## Plan for the next period

| Date | Milestone / activity | Owner |
| --- | --- | --- |
| 22 Sep | M2 — planning documents cross-reviewed and approved | All |
| 23–24 Sep | Case-study analysis → full user story set | Chen Shuai |
| 25 Sep | Jira product backlog built and shared | Chen Shuai / Cao Yang |
| 26–27 Sep | M3 — Sprint 1 committed (8–15 stories) | All |
| 28–30 Sep | M4 — data model and guardian rule designed; README structure | Zhang Runze |
| 1–9 Oct | Development: Member CRUD, Guardian, Registration, Team & Roster, Views | All |
| 9–12 Oct | M6 — tests pass, clean checkout verified | Zhang Runze / Chen Shuai / Zhou Kunpeng |

## Issues requiring attention

1. **Assessment 2 (individual, 40%) is due Monday 5 October** while development is scheduled to finish on 9 October. The A2 requirement must be confirmed immediately and Sprint 1 front-loaded; scope may need to be cut to the five in-scope capabilities.
2. **Two sprints are expected by the unit** (Weeks 3–4 and Weeks 5–6). The current Gantt shows a single development block from 1 to 9 October; the backlog is therefore already split into Sprint 1 (7 stories) and Sprint 2 (6 stories) to match.
3. **Open issues OI-1 to OI-3** (delivery form, persistence approach, same-name edge case) must be closed before M4.

## Assumptions register

| # | Assumption | Impact if wrong |
| --- | --- | --- |
| A-01 | A season starts on 1 March, so a player's age is measured at that date | The guardian rule boundary changes; test cases must be reworked |
| A-02 | The club only needs one active registration per member per season | Duplicate handling logic differs |
| A-03 | Paper forms will be retired; the system becomes the single source of truth | If the paper process continues, duplicate entry is not actually removed and the business case weakens |
| A-04 | PlayRegister remains the association's system of record and is out of scope | Integration work would be required |
| A-05 | Team members have SCU Atlassian and GitHub access | Tooling evidence cannot be produced |
