# Contributing

Four people, one repository, one deadline. Keep it boring and predictable.

## Branch strategy

| Branch | Purpose |
| --- | --- |
| `main` | Always runnable. Protected: no direct pushes, pull request and one approval required. |
| `feature/<wbs-id>-<slug>` | A user story or work package, e.g. `feature/4.1-member-crud`, `feature/4.5-views` |
| `fix/<slug>` | A defect raised in Jira, e.g. `fix/guardian-age-boundary` |
| `docs/<slug>` | Documentation only, e.g. `docs/decision-log-2026-09-25` |

Branches are short-lived. Delete them after merge — a stale branch is a sign the story is
either done or stuck.

## Commit convention

```
<type>(<WBS id>): <imperative summary>

Jira: MSD-<key>
```

| Type | Use for |
| --- | --- |
| `feat` | New user-visible behaviour |
| `fix` | A defect |
| `test` | Tests only |
| `docs` | Documentation only |
| `refactor` | Behaviour-preserving change |
| `chore` | Tooling, dependencies, repository housekeeping |

Examples:

```
feat(4.1): add deactivate instead of hard delete
fix(4.3): treat 18th birthday on season start as adult
test(5.1): cover the under-18 guardian boundary case
docs(6.2): record decision D-06 on deactivation
```

## Pull requests

- One story per pull request. If it needs a paragraph to explain, split it.
- Fill in the template — especially **how it was tested** and **which acceptance criteria it
  satisfies**.
- At least one approving review from a member who did not write the code.
- The CI workflow must be green.
- Squash-merge, then delete the branch.

## Code style

- Python 3.11+, matching the standard library's style (PEP 8, 4-space indents, `snake_case`).
- Type hints on public functions.
- Keep the runtime dependency list empty — the project runs on the standard library. Anything
  added to `requirements.txt` must be development-only and justified in a pull request.

## Tests

- Every behaviour change comes with a test in `tests/`.
- Any change that touches registration must keep the under-18 guardian rule test passing.
- Run before every push: `python -m pytest -q`.
