## 8. Definition of Done

# 07 Definition of Done

A user story is **Done** only when all of the following hold:

1. **Acceptance criteria** — every criterion listed on the Jira story has been demonstrated and the result recorded as a comment on that issue.
2. **Review** — the code was merged through a pull request that was reviewed and approved by at least one other team member.
3. **Automated tests** — new or changed behaviour is covered by an automated test in `tests/`; the full test suite passes.
4. **Guardian rule** — for any story touching registration, the under-18 guardian rule test (including the age boundary) passes.
5. **Clean checkout** — the application runs from a fresh clone using the README alone, with no undocumented steps.
6. **Documentation** — the README, decision log and any affected Confluence page are updated in the same pull request.
7. **Traceability** — the Jira issue records the WBS ID, the story points and the commit or pull-request reference.
