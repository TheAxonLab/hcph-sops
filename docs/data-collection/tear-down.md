# Session tear-down

## Showing the participant out

- [ ] Enter the scanner room, and announce yourself to the participant:

    !!! quote "Hi [NAME], thanks a lot for your collaboration. We will get you out in a second."

- [ ] Extract the participant [following the standard procedure](notes-scanning.md#standard-extraction-of-the-participant).
- [ ] Remove the upper side of the head coil:
    - [ ] Unplug the head coil from the bed connector.
    - [ ] Lift the lever that releases the upper part of the coil and put it aside (e.g., inside the bore or on a chair next to the scanner).
- [ ] Remove the tape band across the coil and touching the participants forehead.
- [ ] Lift the nasal cannula and put it away so the participant can sit down.
- [ ] Assist the participant to remove the padding elements around their head.
- [ ] Help the participant sit down.
- [ ] Instruct the participant to remove the earplugs and dispose of them.
- [ ] Ask them about the experience:

    ???+ quote "Get feedback about the session from the participant"
        [NAME], how was your experience?
        Have you been able to feel comfortable throughout the session?
        What advice, indication do you feel we could've provided you for a better experience?

- [ ] Disconnect the tube from the RB and then lift the velcro attachment to remove the RB.
- [ ] Prepare the belt on the bed to be removed from the room when you show the participant out.
- [ ] Help the participant carefully remove the ECG leads.
- [ ] Disconnect the three ECG leads from the electrodes fixed on the participant's skin.
- [ ] Indicate the participant that they may remove the electrodes outside in the changing room.
- [ ] Bag the ECG leads into their designated self-sealing pouch.
- [ ] Disconnect the last section of the cannula and dispose of it in the trash can.
- [ ] Help the participant step down and accompany them out to the control room.
- [ ] Help the participant recover their personal belongings and change clothes if necessary.
- [ ] Solicit more feedback on participant's comfort for future sessions.
- [ ] Collect `After scan` covariates
    - [ ] Click [this link](https://github.com/{{ secrets.data.covariates_repo | default('<gh_user>/<name>') }}/issues/new?assignees=acionca&labels=mood%2Cafter&projects=&template=mood-questionnaire-after.yml&title=%5BMOOD%5D%5BAFTER%5D+sub-001_ses-yyy), or alternatively
    - [ ] manually open a GitHub Issue at the [questionnaire repository](https://github.com/{{ secrets.data.covariates_repo | default('<gh_user>/<name>') }}):
        - [ ] Under the section `Issues`, click on <span class="consolebutton green">New issue</span>
        - [ ] Select the `Mood questionnaire after scan` template by clicking on <span class="consolebutton green">Get started</span>
    - [ ] Fill in the session id (accessible in the [schedule](participant-prep.md/#session-schedule-reliability))
    - [ ] Ask the participant to fill the rest of the form
- [ ] Solicit tickets and receipts for transportation.
- [ ] Give the participant the corresponding compensation for the participation and transportation.
- [ ] Ask the participant to sign the receipt of the amount of the financial compensation.

## Clearing up the Scanning Room

### ET arm, ET cables, infrared mirror and stimuli screen

- [ ] Unplug the two cables (signal and power) connected to the ET arm.
- [ ] Roll the two ET cables and put them in the cupboard inside the Scanning room.
- [ ] Remove the mirror frame from its rails mounted on the head coil and lay it on the bed.
- [ ] Put the gloves on and cover the infrared mirror for storage.

    !!! danger "The infrared mirror MUST be manipulated with clean gloves at all times."

- [ ] Take the projector's screen off and store it in its designated shelf.

### Gas mask/cannula and tubing, RB and tubing, ECG cables

- [ ] Roll the ECG cable after checking the leads are bagged.
- [ ] Bag the ECG cable once rolled.
- [ ] Detach the RB tube from the RB inlet.
- [ ] Roll the RB tube and the GA tube and store them bagged in the cupboard.

### Readying the scanner for the next session

!!! important "Reset all scanner settings in the Scanning Room to defaults"

    Every setting altered for the experiment MUST be put back to its original status at the end of the experiment (e.g., position of the bed, coil, emergency button, padding elements, etc.)

- [ ] Remove used blankets and bed-sheets <mark>**ONE-BY-ONE**</mark>:
    - [ ] extend them <mark>**ONE-BY-ONE**</mark> to let any forgotten items fall on the floor before you fold it; and
    - [ ] dispose of them <mark>**ONE-BY-ONE**</mark> in the adequate bin (soiled linen bag if they are fabric and trash if they are disposable).

    ??? danger "Make sure you do not accidentally dispose of valuable items or instrumentation"

        At the end of the scanning session everyone is tired and the likelihood of a misshapen is large because the attention levels are at their lowest.
        Stay focused during the tear-down.

- [ ] Dispose of all single-use sanitary protections (padding covers, earplugs, etc.).
- [ ] Put the pillows back in their designated storage places.
- [ ] Remove the head coil and put it in the scanner's bore.
- [ ] Remove the back padding elements and put them back in their designated storage.
- [ ] Reinstall the spine coil.
- [ ] Wipe the bed and the head coil (bottom and upper parts).

    !!! info "Cleaning wipes are available on shelf in the Scanning Room."

- [ ] Lock the head coil back with its bottom part without plugging the connectors.
- [ ] Put the head coil away with the other head-coils on the shelf next to the scanner.

    !!! important "If the next user is already there or you know the current coil will be also used in the next session, plug it back into the bed socket."

- [ ] Return the bed to its *Home* position by pressing the :fontawesome-solid-house: button ([more info](notes-scanning.md#standard-extraction-of-the-participant)).
- [ ] Take the ET arm outside to the Control Room and place it in a stable place.
- [ ] Take the infrared outside to the Control Room and store it in the ET/fMRI box.
- [ ] Take the plexiglass panel outside to the control room.
- [ ] Take the RB outside the scanning room and box it in the ET/fMRI box.
- [ ] Exit and close the external door.

## Synchronize collected physiological data (eye-tracking and BIOPAC signals)

**On the *stimuli laptop ({{ secrets.hosts.psychopy | default("███") }})*:**

- [ ] Copy data from the `{{ secrets.psychopy_paths.data }}` subfolder in *{{ secrets.hosts.psychopy | default("███") }}* into the synchronized Dropbox folder `{{ secrets.psychopy_paths.dropbox }}`.

    ??? danger "This reports what we did, but the setup MUST be updated to directly write into the synchronized folder."

        *Psychopy* forcefully writes eye-tracking data into the `./data` folder of the experiment file.
        In our case that means `{{ secrets.psychopy_paths.tasks }}/data`, which is a softlink to `{{ secrets.psychopy_paths.data }}`.
        For future data collection efforts, the softlink should change to point directly to `{{ secrets.psychopy_paths.dropbox }}`.

- [ ] Check that the computer is connected to the Internet and *Dropbox* initiates synchronization.

**On the *physiology recording laptop ({{ secrets.hosts.acqknowledge | default("███") }})*:**

- [ ] Disconnect the Ethernet cable from the adaptor dongle attached to *{{ secrets.hosts.acqknowledge | default("███") }}*.
- [ ] Enable the Wireless connection, as it will be disabled to permit communications with the BIOPAC.
- [ ] Check Internet access and that *Dropbox* initiates synchronization.

## Clearing up the Control Room

### Finalize the *boxing* of the ET elements

- [ ] Put the lens cover.
- [ ] Unscrew the ET lens, while **ALWAYS** keeping one hand under the lens while screwing/unscrewing it, put back its cover and put the lens back into its pouch.
    ![cover-mri-compatible-lens](../assets/images/cover-mri-compatible-lens.png "Cover MRI compatible lens")
- [ ] Store the ET arm in its designated box.

    !!! danger "REMEMBER | the infrared mirror is inside that box already: DO NOT crush the mirror."

- [ ] Store the *fMRI box* back in room {{ secrets.rooms.et_camera| default("███") }}.

### Finalize the *boxing* of other physiological recording instruments

- [ ] Disconnect the bundle of cables coming out of the access panel in the Control Room (Ethernet from the ET PC, USB from MMBT-S Interface and power strip cable plug).
- [ ] Roll the bundle and place it at the bottom shelf.
- [ ] Disconnect the Ethernet cable of the BIOPAC from the *{{ secrets.hosts.acqknowledge | default("███") }}* computer.
- [ ] Disconnect the *AcqKnowledge USB License Key* from the *{{ secrets.hosts.acqknowledge | default("███") }}* computer and bag it (pink bag next to the BIOPAC unit).
- [ ] Retrieve the *{{ secrets.hosts.acqknowledge | default("███") }}* computer from the closet and put it on the control desk.
    - [ ] Retrieve the power cord and plug if they are set.

### Finalizing the support laptops

- [ ] Unplug from {{ secrets.hosts.psychopy | default("███") }} the USB cable coming from the SyncBox.
- [ ] Switch the SyncBox off, and make sure you leave it connected exactly as you found it.
- [ ] Unplug from {{ secrets.hosts.psychopy | default("███") }} the HDMI cable from the display switch.
- [ ] Check that you leave the display switch as you found it.
- [ ] Switch off the {{ secrets.hosts.psychopy | default("███") }} computer.
- [ ] Exit the *Amphetamine* session and lock the screen of the {{ secrets.hosts.acqknowledge | default("███") }} computer.

### Switching off the projector

- [ ] Take the plexiglass panel back into room {{ secrets.rooms.projector | default("███") }}.
- [ ] Switch the projector off before exiting room {{ secrets.rooms.projector | default("███") }}.

---

**If no more sessions are scheduled afterward**:

- [ ] [Turn off the MRI system](notes-scanning.md#scanner-shutdown-protocol).
