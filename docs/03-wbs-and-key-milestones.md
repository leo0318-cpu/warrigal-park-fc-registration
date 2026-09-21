## 4. WBS and Key Milestones

# 03 WBS and Key Milestones

## Decomposition rules

- **Deliverable-oriented:** the WBS decomposes deliverables and work packages, not process activities.
- **Levels:** L1 the whole project; L2 the seven phases; L3 the individual work packages.
- **8/80 rule:** every work package is sized between 8 and 80 hours.
- **Project Management is a separate branch**, approximately 12% of total effort.

## WBS structure

```
Warrigal Park FC Member Registration & Team Roster System
├─ 1.0 Project Management (Cao Yang) — ~12% of effort
│   ├─ 1.1 Project initiation documents (Charter, minutes) — Cao Yang / Chen Shuai
│   ├─ 1.2 WBS, milestones and Gantt chart planning — Zhou Kunpeng
│   └─ 1.3 Team meetings, risk tracking, Confluence maintenance — Cao Yang
├─ 2.0 Requirements Analysis and Backlog Management (Chen Shuai)
│   ├─ 2.1 Case study analysis, derive all user stories — Chen Shuai
│   ├─ 2.2 Jira setup, build the product backlog — Chen Shuai / Cao Yang
│   └─ 2.3 Sprint backlog selection (8–15 stories, 1–2 epics) — All
├─ 3.0 System Design (Zhang Runze)
│   ├─ 3.1 Data model design (Member / Guardian / Registration / Team) — Zhang Runze
│   ├─ 3.2 Business rule design (mandatory guardian for under-18s) — Zhang Runze / Chen Shuai
│   └─ 3.3 README and project directory structure design — Zhang Runze
├─ 4.0 Development (Zhang Runze, with Chen Shuai / Zhou Kunpeng)
│   ├─ 4.1 Member CRUD, persistence, search by name (incl. same-name) — Zhou Kunpeng
│   ├─ 4.2 Guardian entity, one-to-many links, sync updates across children — Zhang Runze
│   ├─ 4.3 Season registration, status flow, guardian rule validation — Chen Shuai
│   ├─ 4.4 Team creation, place/move/remove players, rosters — Zhang Runze
│   └─ 4.5 Views (roster + contacts, registration history, guardian's juniors) — Zhou Kunpeng
├─ 5.0 Testing (Zhang Runze)
│   ├─ 5.1 Unit automated tests (guardian rule focus) — Zhang Runze
│   ├─ 5.2 End-to-end tests covering acceptance criteria — Chen Shuai / Zhou Kunpeng
│   └─ 5.3 Clean-checkout verification — All
├─ 6.0 Delivery Preparation (Cao Yang)
│   ├─ 6.1 GitHub repository, branch and PR review workflow — Zhang Runze
│   ├─ 6.2 Confluence documentation: assumptions, decision records — Chen Shuai
│   └─ 6.3 Sprint-close handover documentation (six sections) — Cao Yang / All
└─ 7.0 Project Closure (Cao Yang)
    ├─ 7.1 Deliverables consolidation and finalisation — Cao Yang
    └─ 7.2 Retrospective, known limitations, next-iteration recommendations — All
```

## Work packages

| WBS ID | Work package | Owner | Estimate |
| --- | --- | --- | --- |
| 1.1 | Project initiation documents | Cao Yang / Chen Shuai | 2 days |
| 1.2 | WBS, milestones and Gantt chart | Zhou Kunpeng | 3 days |
| 1.3 | Team meetings, risk tracking, Confluence maintenance | Cao Yang | Ongoing |
| 2.1 | Case study analysis, derive all user stories | Chen Shuai | 2 days |
| 2.2 | Jira setup, build the product backlog | Chen Shuai / Cao Yang | 1 day |
| 2.3 | Sprint backlog selection (8–15 stories) | All | 2 days |
| 3.1 | Data model design (four entities) | Zhang Runze | 2 days |
| 3.2 | Business rule design (guardian validation) | Zhang Runze / Chen Shuai | 1 day |
| 3.3 | README and directory structure design | Zhang Runze | 1 day |
| 4.1 | Member CRUD, persistence, search | Zhou Kunpeng | 3 days |
| 4.2 | Guardian entity, one-to-many links, sync | Zhang Runze | 3 days |
| 4.3 | Season registration, status flow, guardian validation | Chen Shuai | 3 days |
| 4.4 | Team creation, place/move/remove players, roster | Zhang Runze | 3 days |
| 4.5 | Views development (roster / history / juniors) | Zhou Kunpeng | 2 days |
| 5.1 | Unit automated tests (guardian rule) | Zhang Runze | 2 days |
| 5.2 | End-to-end tests (acceptance criteria) | Chen Shuai / Zhou Kunpeng | 1 day |
| 5.3 | Clean-checkout verification | All | 1 day |
| 6.1 | GitHub maintenance, branch and PR review | Zhang Runze | Ongoing |
| 6.2 | Confluence documentation | Chen Shuai | Ongoing |
| 6.3 | Handover documentation (six sections) | Cao Yang / All | 2 days |
| 7.1 | Deliverables consolidation and finalisation | Cao Yang | 1 day |
| 7.2 | Retrospective and next-iteration recommendations | All | 1 day |

## Key milestones

| ID | Milestone | Acceptance / deliverable | Planned date | Status |
| --- | --- | --- | --- | --- |
| M1 | Project kick-off complete | Kick-off held; minutes finalised | 2026-09-20 | **Achieved** |
| M2 | Planning documents approved | Four planning documents cross-reviewed | 2026-09-22 | In progress |
| M3 | Requirements approved | Sprint backlog of 8–15 stories with acceptance criteria | 2026-09-27 | Not started |
| M4 | Design approved | Data model and business rule designed and reviewed | 2026-09-30 | Not started |
| M5 | Development complete | All committed stories merged to `main` | 2026-10-09 | Not started |
| M6 | Testing complete (DoD met) | All tests pass; clean-checkout verified | 2026-10-12 | Not started |
| M7 | Delivery preparation complete | Handover document (six sections) + PDF export | 2026-10-14 | Not started |
| M8 | Project closure | Retrospective complete; all deliverables final | 2026-10-15 | Not started |

## Timeline

| Phase | Dates | Content |
| --- | --- | --- |
| Planning | 2026-09-18 → 2026-09-22 (5 days) | Roles, charter, kick-off, WBS, Gantt |
| Sprints (development + testing) | 2026-09-23 → 2026-10-13 | Backlog definition → design → development → testing |
| Closure | 2026-10-14 → 2026-10-15 | Handover documentation, retrospective |
