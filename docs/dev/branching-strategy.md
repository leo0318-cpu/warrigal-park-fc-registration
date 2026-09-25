# Version control and branching strategy

Assignment 2 (Configuration Management Report) asks for the branching model this project
actually uses. This page is that model. It is written before the code so that the report
describes real practice rather than a retrospective invention.

## Repository layout

One repository, one `main` branch, and one or more `feature/*` branches — one branch owned
by each team member.

| Branch | Owner | Work package | Contents |
| --- | --- | --- | --- |
| `main` | shared | — | Only work that is complete, reviewed and tested |
| `feature/member-crud` | Zhou Kunpeng | WBS 4.1 | Member create / find / update / deactivate, name search |
| `feature/member-views` | Zhou Kunpeng | WBS 4.5 | Roster + contacts, registration history, guardian's juniors |
| `feature/guardian-links` | Zhang Runze | WBS 4.2 | Guardian entity, one-to-many links, sync across children |
| `feature/team-roster` | Zhang Runze | WBS 4.4 | Team creation, place / move / remove players |
| `feature/season-registration` | Chen Shuai | WBS 4.3 | Season registration and the status flow |

Each member creates their own branch from `main` and works only on that branch. Branches
belonging to other members are not to be pushed to on their behalf.

## Rules

1. **`main` is never edited directly.** Every change reaches `main` through a pull request.
2. **A branch carries one work package.** Mixing WBS 4.1 and 4.5 in one branch makes review
   and rollback impossible.
3. **A pull request needs a reviewer who is not the author.** With four members this is
   always achievable.
4. **Merge only when the Definition of Done is met**: the acceptance criteria of the linked
   story are demonstrably satisfied, automated tests pass, and the README reflects the change.
5. **Commit messages name the work package**, e.g. `docs(4.1): ...`, `feat(4.3): ...`.
6. **Configuration is not committed.** Environment-specific values live in a template that is
   committed; the filled-in file is not. See Deployment Configuration below.

## Deployment configuration

| Configuration item | Where it lives | Committed? |
| --- | --- | --- |
| `config.env.template` | repository root | Yes — the canonical list of settings |
| `config.env` | local only | No — ignored, holds real values |
| `requirements.txt` | repository root | Yes — pins the tool versions |
| `deploy.sh` | repository root | Yes — one command from a clean clone to a running application |
| `CHANGELOG.md` | repository root | Yes — what changed and when |

A clean-checkout verification (WBS 5.3) clones the repository on a machine that has nothing
pre-installed and runs `deploy.sh` using only the README. If that fails, the Definition of
Done is not met regardless of whether tests pass locally.
