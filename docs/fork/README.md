# EV Nova fork work

The goal is to play stock Nova on a current Mac and contribute fixes supported by a repeatable comparison. This branch tracks independent changes on the fork. [QA findings](findings.md) records what each experiment established. [Test plan](plan.md) gives the next checks.

## Queue

Snapshot on 2026-11-21. All five branches below are based on upstream `e3dd304`.

| Work | State | Next decision |
| --- | --- | --- |
| [Save on quit from a spaceport](https://github.com/arclabs561/evnova-decomp/tree/mission-resume-qa) · `4b052b5` | First submission candidate. A normal quit can lose progress. Linux reproduced the loss and verified the fix across a restart. | Review the paired scenarios and test the native macOS Quit action. |
| [Skip unused ship effect masks](https://github.com/arclabs561/evnova-decomp/tree/additive-ship-textures) · `f02e36b` | Second candidate. A controlled renderer test reduced peak memory with identical pixels. | Verify fog and hypergate emergence on Apple Silicon. |
| [Keep the failed scenario step](https://github.com/arclabs561/evnova-decomp/tree/scenario-failure-report) · `94f47b6` | Independent tooling fix. Preserves the original expectation when the probe disappears. | Review a failure artifact from a nested scenario. |
| [Compare screenshots in scenarios](https://github.com/arclabs561/evnova-decomp/tree/visual-scenario-checks) · `5bbf2d1` | Fork QA tool. Passed a live positive check and detected an intentional mismatch. | Find a gameplay regression that a state assertion misses before proposing this upstream. |
| [Fix special cargo selection](https://github.com/wraitii/evnova-decomp/pull/4) · `bcd6f8c` | Upstream PR #4 is open. Both Trade Center rows select the highest eligible cargo ID. | Follow maintainer review and Actions status on the PR. |

The Drive folder **Gameplay captures and upstream review** holds the evidence. Its index is `Upstream-review.md`. Use the filenames in the findings to locate individual experiments.
