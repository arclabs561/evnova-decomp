# Submission drafts

## Save the pilot when quitting from a spaceport

Quitting on Mars could reload the pilot at the previous port. Run the dock autosave on quit, just as Nova does on launch. I verified that the mission survived a restart and could be finished on Earth.

**Review note.** Verified with a Linux probe quit. Native Mac application-menu Quit remains open.

## Check which store item is selected

The purchase scenarios could accept Heavy Shuttle while Shuttle was highlighted. Check the label on the selected item before buying a ship, outfit, or escort.

**Review note.** Reproduced both wrong selections in Earth's shipyard. The runner regression uses synthetic rows and can run in CI without game data.

## Follow-up

At some ports the probe lists rectangles for hidden services. The spaceport draws and activates services using `ServiceAvailable`, while its probe publication loop emits every slot. Before changing that contract, check the scenarios that click Refuel unconditionally, including visits with a full tank.
