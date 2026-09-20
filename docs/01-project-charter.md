## 2. Project Charter

# 01 Project Charter — V1.0

**Project:** Warrigal Park FC Member Registration & Team Roster System
**Project ID:** ASG3-M1 · **Version:** V1.0 · **Date:** 20 September 2026
**Sponsor:** Course team (simulating the Warrigal Park FC committee)
**Project Manager:** Cao Yang

## 1. Background and business value

Warrigal Park Football Club Inc. is a community club at Bald Hills on Brisbane's northern edge that has fielded teams every season since 1978. Registration today runs on paper forms, a 43-column Excel master spreadsheet, a second data-entry pass into the association's PlayRegister system, and manual distribution of age-group lists.

**Problems to solve**

1. The same registration details are typed multiple times, inviting transcription errors.
2. Forms come back unreadable or with the guardian section blank; siblings are entered twice and players sharing a name are confused.
3. In 2024 a player took the field whose registration had not gone through, raising an insurance-liability risk (association circular, item 4).
4. Registration statistics are counted by hand and team nominations to the association are chronically submitted at the last minute (1 March).

## 2. Measurable success criteria

| ID | Criterion |
| --- | --- |
| S1 | Full create / find / update / deactivate of members is supported |
| S2 | The mandatory guardian business rule is enforced and provably tested |
| S3 | A single guardian can be linked to multiple juniors and updated once |
| S4 | Every committed user story satisfies its recorded acceptance criteria |
| S5 | A runnable version is delivered that runs from a clean checkout using the README alone |
| S6 | The system costs nothing to run (free tool stack, no paid services) |

## 3. Scope

**In scope**

| Capability | Description |
| --- | --- |
| Member | Create, find, update and deactivate members |
| Guardian | Create, find and update guardians; link a guardian to one or more juniors |
| Registration | Players register for a season with a status flow (Started / Complete / Withdrawn) |
| Team & Roster | Create a team for a season; place, move and remove players |
| Views | Team roster with contacts; registration history; a guardian's juniors |
| Project deliverables | GitHub repository, Jira product backlog, Confluence documentation set |

**Out of scope (moved to the product backlog; not built this iteration)**

Fees and finance; PlayRegister integration; compliance checks (Blue Card / Working with Children); squad and age validation; fixtures, results and ladders; canteen roster, uniforms and merchandise.

**Constraints**

- Budget $0 — free tool stack only (GitHub Free, Jira Free, Confluence Free, Python standard library)
- A runnable version must be delivered by the end of the iteration
- Delivered as a Python command-line application
- A player under 18 cannot complete registration without a linked guardian
- Minors' privacy must be protected — no unnecessary personal data stored
- Four-person team; one member may be on placement

## 4. Stakeholders

| Stakeholder | Role | Interests |
| --- | --- | --- |
| Vanessa Ostrowski | Club Registrar (primary user) | Data quality, no duplicate entry, fast registration |
| Danny Sok | Junior Coordinator (U13 Girls) | Players by age group, moving players between teams |
| Robyn Iyer | Club President | Registration totals by age group, on-time nominations |
| Association (NFA) | External constraint | PlayRegister remains mandatory |

## 5. Feasibility

| Dimension | Conclusion | Basis |
| --- | --- | --- |
| Technical | Feasible | Small CRUD application plus one validation rule; standard library is sufficient |
| Economic | Feasible | Entire tool stack is free |
| Operational | Feasible | Handover is code + README + handover document |
| Schedule | Feasible | Two weeks planning plus three weeks of sprints before the 19 October deadline |

## 6. High-level risks

| Risk | Impact | Mitigation |
| --- | --- | --- |
| R1 Guardian rule implemented incorrectly | Violates the club's core rule; child-safety and insurance exposure | A standalone automated test for the rule, including the age boundary |
| R2 Scope creep (fees, SMS, fixtures) | Committed scope becomes undeliverable | Out-of-scope list explicit in the charter and the README |
| R3 Team scheduling conflicts | Delivery slips | Sprint backlog limited to 8–15 stories; buffer before the deadline |
| R4 Documentation and code drift apart | Definition of Done not met; handover fails | DoD requires a clean-checkout run using the README alone |
| R5 Case information scattered across interviews and documents | Acceptance criteria diverge from what the club actually needs | Cross-check the three interviews and the three paper documents |

## 7. Milestones overview

M1 Kick-off complete → M2 Planning documents approved → M3 Requirements approved → M4 Design approved → M5 Development complete → M6 Testing complete → M7 Delivery preparation complete → M8 Project closure. Detail in *03 WBS and Key Milestones*.

## 8. Approval

| Name | Role | Date |
| --- | --- | --- |
| Cao Yang | Project Manager | 2026-09-20 |
| Chen Shuai | Business / Requirements Lead + Scribe | 2026-09-20 |
| Zhang Runze | Technical Lead | 2026-09-20 |
| Zhou Kunpeng | Scheduling Lead | 2026-09-20 |
