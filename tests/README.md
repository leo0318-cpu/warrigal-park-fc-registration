# Tests

| Area | WBS | Owner | What belongs here |
| --- | --- | --- | --- |
| Guardian rule | 5.1 | Zhang Runze | `test_guardian_rule.py` — under-18 without a guardian is rejected; the 18th-birthday boundary is treated as adult |
| Member CRUD | 5.1 | Zhou Kunpeng | create / find (including same-name) / update / deactivate |
| Guardian links | 5.1 | Zhang Runze | one guardian, several juniors; a single update propagates |
| Registration and roster | 5.2 | Chen Shuai | status flow, duplicate registration refused, move never leaves a player on two rosters |
| Views | 5.2 | Zhou Kunpeng | roster with contacts, registration history, guardian's juniors, empty states |

Run everything with:

```bash
python -m pytest -q
```
