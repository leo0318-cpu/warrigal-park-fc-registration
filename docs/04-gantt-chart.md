## 5. Gantt Chart

# 04 Gantt Chart

**Source file:** `04_Project_Gantt_Chart.xlsx` (attached below)

## How to read it

- Sheets: `Gantt Chart` (schedule view) and `Task List` (detail view).
- 24 tasks (P1–C2) plus 8 milestones (M1–M8); weekdays only — weekends are left blank by design.
- Bars: task duration `#5B9BD5`; milestone markers ◆ placed on the planned milestone date.

## Task summary

| ID | WBS | Task | Owner | Start | End | Days | Depends on |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P1 | 1.1/2.1 | Task breakdown and role assignment (read case study) | All | 09-18 | 09-18 | 1 | – |
| P2 | 1.1 | Draft Project Charter + feasibility analysis | Cao Yang / Chen Shuai / Zhang Runze | 09-19 | 09-19 | 1 | P1 |
| P3 | 1.3 | Kick-off meeting + meeting minutes | All | 09-20 | 09-20 | 1 | P2 |
| P4 | 1.2 | WBS decomposition + dependency mapping | Zhang Runze / Zhou Kunpeng | 09-21 | 09-21 | 1 | P3 |
| P5 | 1.2 | Scheduling, Gantt chart + cross-review finalisation | Zhou Kunpeng / All | 09-22 | 09-22 | 1 | P4 |
| R1 | 2.1 | Deep case analysis, derive user stories | Chen Shuai | 09-23 | 09-24 | 2 | P5 |
| R2 | 2.2 | Jira setup + build product backlog | Chen Shuai / Cao Yang | 09-25 | 09-25 | 1 | R1 |
| R3 | 2.3 | Sprint backlog selection (8–15 stories) | All | 09-26 | 09-27 | 2 | R2 |
| D1 | 3.1 | Data model design (four entities) | Zhang Runze | 09-28 | 09-29 | 2 | R3 |
| D2 | 3.2 | Business rule design (guardian validation) | Zhang Runze / Chen Shuai | 09-29 | 09-29 | 1 | D1 |
| D3 | 3.3 | README and directory structure design | Zhang Runze | 09-30 | 09-30 | 1 | D1 |
| DEV1 | 4.1 | Member CRUD, persistence, search | Zhou Kunpeng | 10-01 | 10-03 | 3 | D1 |
| DEV2 | 4.2 | Guardian entity + links + sync | Zhang Runze | 10-02 | 10-04 | 3 | D2 |
| DEV3 | 4.3 | Season registration + status flow + guardian rule | Chen Shuai | 10-04 | 10-06 | 3 | D2 |
| DEV4 | 4.4 | Team creation + add/move/remove players | Zhang Runze | 10-06 | 10-08 | 3 | DEV1 |
| DEV5 | 4.5 | Views (roster / history / juniors) | Zhou Kunpeng | 10-08 | 10-09 | 2 | DEV3 |
| T1 | 5.1 | Unit tests (guardian rule) | Zhang Runze | 10-09 | 10-10 | 2 | DEV2 / DEV3 |
| T2 | 5.2 | End-to-end tests (acceptance criteria) | Chen Shuai / Zhou Kunpeng | 10-11 | 10-11 | 1 | T1 |
| T3 | 5.3 | Clean-checkout verification | All | 10-12 | 10-12 | 1 | T2 |
| H1 | 6.1 | GitHub maintenance + PR review (ongoing) | Zhang Runze | 10-01 | 10-12 | 12 | – |
| H2 | 6.2 | Confluence documentation (ongoing) | Chen Shuai | 10-08 | 10-13 | 6 | D1 |
| H3 | 6.3 | Handover documentation (six sections) | Cao Yang / All | 10-13 | 10-14 | 2 | T3 |
| C1 | 7.1 | Deliverables consolidation and finalisation | Cao Yang | 10-14 | 10-14 | 1 | H3 |
| C2 | 7.2 | Retrospective + next-sprint recommendations | All | 10-15 | 10-15 | 1 | C1 |
