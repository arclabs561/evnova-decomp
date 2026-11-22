# Playing Nova to find regressions

Give the agent a player goal with an observable outcome. Keep the pass condition fixed before play. The agent chooses inputs based on the current screen; a separate check decides whether the game honored them. A scripted route can be checked with the same assertions.

## First playable goal

Start in Earth's shipyard with a disposable pilot, at the same renderer, size and page used for the reviewed Heavy Shuttle frame. On the agent-play-qa branch run:

    python3 tools/play_shipyard.py 'Heavy Shuttle' /path/to/store.slot.1.bmp /tmp/shipyard-attempt-01

The directory must be new. The controller reads the live UI, chooses whether to click, sends at most one named click, verifies that exactly the requested row is selected, and compares the visible cell with a reviewed reference. It records the observed rows, action and verdict. A mismatch also retains the visual diff when available. This goal ends before purchase. A different renderer or layout needs its own reviewed reference. A disabled probe, missing reference or wrong starting screen is an unusable run for parity comparisons.

## Expand by one player decision at a time

1. Buy an affordable item with a disposable pilot. Record the quoted price, starting credits and inventory. Verify the exact debit and the acquired item. Use the existing scenario runner for reproducible setup. In exploratory play, read the active modal and available items before choosing an action. Pick a named row or key, then wait for the expected result. Stop on an unexpected modal or exhausted action budget and retain its frame. Keep deliberate wrong selections as negative controls.
2. Save and restart. A process supervisor owns the disposable profile, launches the game twice and checks process exit and probe readiness. Run the existing mission_save and mission_resume scenarios from the save-on-quit branch against the same profile. Add the purchased item and remaining credits to the restart assertions. Steering, landing and store clicks exercise game code; direct edits to a pilot belong only in fixture preparation. Native macOS Quit needs its own OS-input run.
3. For the failed-write regression, start with a verified loadable pilot. Inject failure only into the second save, end the process, then restart without the fault. The prior pilot must load with its original inventory and credits. This is a separate test from the regular save path. Avoid file-size limits on an entire gameplay process when logs or supporting files could also hit the limit.
4. Advance one stock mission chain. Let the agent handle the offered dialog or route; verify the specific mission ID, completion, payout and subsequent offer. Capture a short replay for a failure. Reproduce on upstream and on the fix from the same fixture before promoting it to a PR.

For a run worth retaining, record build SHA, data version, renderer and scale, initial pilot digest, action sequence, observed outcome and the expected outcome's source. Keep raw frames, saves and evidence in Drive. Store portable scenarios and their assertions on the fork. Treat an unexpected outcome as a candidate until the original game, an independently documented rule or a well-defined persistence invariant establishes the expected behavior.
