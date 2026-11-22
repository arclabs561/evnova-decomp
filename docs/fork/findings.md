# QA findings

Tests below used stock Community Edition data with the Linux SDL software renderer unless otherwise stated.

| Experiment | Result | Evidence or replay |
| --- | --- | --- |
| Quit on Mars during Barry's first delivery, restart, finish on Earth | Before the fix a pilot returned to Fomalhaut. After the fix the pilot resumed in Sol and finished the mission. A separate Trade Center quit preserved purchased cargo. | `mission_save.toml` and `mission_resume.toml` on the save branch |
| Sell one ton at Latin | The game removed Bio-Engineered Kelp and paid 125 credits. The original Windows selection routine under QEMU picked the same eligible cargo. | PR #4 and Drive review |
| Reload a freight job and fly to Fermia | The destination and one-ton load survived restart. Delivery paid the promised 5,000 credits. | Drive review and session notes |
| Render 25 additive ship sheets | All 2,088 frames matched byte-for-byte at two fog settings. Peak process RSS fell from 402,020 to 277,720 KiB in this controlled workload. | `ship-texture-qa.zip` |
| Visit Mars and Earth eight times each | By the final four stops, 34 ship classes had loaded. RSS held at 641 MiB and the tracked static texture count held at 11,664. Earlier process kills still have no confirmed cause. | `observations.csv` in `visual-qa-replay.zip` |
| Switch between Shuttle and Heavy Shuttle at Earth | A visible hull name and a highlight on a different hull satisfied the old guard. Reversing the choice reproduced the same false pass. The corrected guard rejected both. A separate capture of the correct highlight matched exactly; the other selection differed by 219 pixels in the 84 × 55 cell. | `shipyard-selection-qa.zip` |
| Compare an independent Port Kane capture | The Leave button matched exactly. Using Earth as a reference changed 195,654 pixels despite both screens reporting the spaceport state. | `port-comparison.png` and `visual-qa-replay.zip` |

The save branch passed 863 tests in each Linux build configuration. The texture branch passed 864, including its new regression. Each suite skipped two optional pilot-fixture tests. Native Mac gameplay and graphics measurements are still open.

## Live purchase and failed overwrite

[Purchase/restart driver](https://github.com/arclabs561/evnova-decomp/tree/purchase-restart-qa) and [pilot preservation fix](https://github.com/arclabs561/evnova-decomp/tree/preserve-pilot-save). Four Linux game runs used disposable stock pilots. With the quit fix alone, ten tons of Food and 24,400 credits loaded after a normal quit at Ryll. A 4,096-byte process file limit applied immediately before quitting at Moonview truncated the existing 86,120-byte pilot and the next process had no active pilot. Adding staged replacement preserved the previous file byte-for-byte under that limit and restored the initial 25,000 credits and empty holds. Its successful control restored ten tons and 24,250 credits at Moonview. Drive evidence: `trade-restart-live.zip`. Native Mac and Windows replacement, file metadata preservation and abrupt power loss remain unverified.

At `d65fbc0` on `preserve-pilot-save`, Linux preserved modes 0600 and 0640 and rejected the read-only 0444 pilot. The initial staging implementation replaced all three with 0644. The linked regression passed seven assertions. Two live restarts on the quit-fix integration restored the purchase normally and retained the original pilot after a forced short write. Evidence: `pilot-overwrite-modes.zip`. The probe verifies POSIX mode bits only; extended ACLs, ownership, hard links and power-loss behavior remain open.
