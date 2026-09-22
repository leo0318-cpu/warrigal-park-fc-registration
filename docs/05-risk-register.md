## 6. Risk Register

# 05 Risk Register

*Reviewed at the weekly sync. Probability / Impact scored 1 (low) to 5 (high); Exposure = P × I.*

| ID | Risk | P | I | Exp | Owner | Mitigation / response | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| R1 | Guardian rule for under-18s implemented incorrectly | 3 | 5 | 15 | Zhang Runze | Dedicated automated unit test including the age boundary (US-08, WBS 5.1) | Open |
| R2 | Scope creep — fees, PlayRegister integration, fixtures requested mid-sprint | 4 | 4 | 16 | Cao Yang | Explicit Out-of-Scope list in the charter and README; new requests go to the product backlog, not the sprint | Open |
| R3 | Team scheduling conflicts / one member on placement | 3 | 4 | 12 | Cao Yang | Sprint backlog capped at 8–15 stories; two-day buffer before 19 October | Open |
| R4 | Documentation and code drift apart | 3 | 4 | 12 | Zhang Runze | Definition of Done requires a clean-checkout run using the README alone | Open |
| R5 | Case information scattered across interviews and paper documents | 3 | 3 | 9 | Chen Shuai | Cross-check the three interviews and three paper documents; record assumptions | Open |
| R6 | A2 (individual, 40%) falls due 5 October while development is still running | 4 | 5 | 20 | Zhou Kunpeng | **Raised 22 Sep** — confirm A2 requirements immediately; front-load Sprint 1 and be prepared to cut scope to the five in-scope capabilities | Open |

**Open issues carried from the kick-off**

| ID | Issue | Owner | Due | Status |
| --- | --- | --- | --- | --- |
| OI-1 | Delivery form: Python CLI vs web | Zhang Runze | 2026-09-21 | Open |
| OI-2 | Persistence: SQLite vs JSON | Zhang Runze | 2026-09-22 | Open |
| OI-3 | Same-name edge case with no date of birth | Chen Shuai | 2026-09-22 | Open |
| OI-4 | Shared document platform | Cao Yang | 2026-09-20 | Closed — Confluence |
