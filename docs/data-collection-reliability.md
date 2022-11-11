

### Scheduling

#### One week BEFORE THE FIRST SESSION

- [ ] Send a copy of the MRI Safety and screening form to the participant over email and confirm reception
- [ ] Confirm that participant has read and understood the document, and in particular, double-check that they do not have any MRI contraindications
- [ ] Remind participant that any jewelry should be removed prior to the scan 
- [ ] Confirm clothing:
  - [ ] if allowed to wear street clothes, remind participant to avoid clothing with metal or that would uncomfortable to lie in for the duration of the scan; otherwise
  - [ ] remark the participant they will be given a gown and they will need to change before every session.
- [ ] If participant has indicated nervousness or history of claustrophobia, utilize mock scanner 

#### DAY OF SCAN, prior to participant arrival

- [ ] Prepare consent documents (first session only)
- [ ] Prepare an MRI safety screener 
- [ ] Prepare scrubs and MR-compatible glasses if applicable
- [ ] Setup scanner room and peripherals:
  - [ ] prepare the 64-channel headcoil, with the mirror for movie projection
  - [ ] Turn on the projector in the room BH07.075
  - [ ] prepare paddings: under-knee padding, neck padding, inflatable head-paddings
  - [ ] prepare a blanket
  - [ ] prepare a new pair of earplugs
  - [ ] prepare the respiration belt, as well as the placeholder for the ECG and other physio sensors
  - [ ] connect the cable from the RJ-45 output of the syncbox to the first filter (VNC connector; has a label "External signal") in the cupboard covering the access panel to the Faraday cage. The cable might be stored in the lower left cupboard of office 071. Make sure you will have access to the cable with sufficient time ahead.
    - [ ] On the scanner console, checke the external signal input registers triggers from the syncbox
    - [ ] prepare a thermometer
    - [ ] prepare a blood preasure meter
  - [ ] Setup the syncbox
    - [ ] connect the USB cable from the syncbox to the PC HOS54938 (next to the DVD printer/burner)
    - [ ] enter the user (password is on the computer)
    - [ ] open the *.es2 file 
    - [ ] On the syncbox click "synchronisation"
    - [ ] the script tells you how to configure the syncbox (e.g trigger every 10 volumes)

  - [ ] Set up the eye-tracking:
    - [ ] 
  - [ ] Open psychopy 3 and this protocol's files, make sure you have internet access to a Git repository and check files are up-to-date.
  - [ ] Prepare the gas-analyzer:
    - [ ] Prepare the canule tube, which is introduced through the tube in the access panel
    - [ ] Prepare a new canule
- [ ] Check stimulus display and response device:
  - [ ] Check the movie to be displayed is ready
  - [ ] Check the execution of the Breath holding task
  - [ ] Check the execution of the finger tapping task

#### DAY OF SCAN, right when the participant arrives

- [ ] Have participant fill out consent documents and MRI safety screener, and verbally confirm responses, paying attention to frequently forgotten devices and implants, like orthodontia
- [ ] Have the participant report 
  - [ ] the time at which the last coffee was consumed
  - [ ] the time at which the last meal was consumed
  - [ ] the consumption of substances that may introduce variability in the analysis (e.g., 5-HT1A receptor agonists for cluster headaches)
  - [ ] the naked weight (measured by the participant at home before the session)
- [ ] Measure and report
  - [ ] The participant's blood pressure with the Omron M3 Comfort device while sitting down 
  - [ ] The participant's body temperature
  - [ ] The scanning room temperature
  - [ ] The scanning room pressure with an MRI-compatible barometer
- [ ] Have participant empty their pockets or change into scrubs, and remove all jewelry/hair accessories and check for any missed metallic objects with the scan center’s preferred method
- [ ] Instruct participant on staying still and encourage them to request breaks if necessary
- [ ] Describe the participant how the session will develop, with special attention to tasks. Answer all the questions that may arise.
- [ ] Show the alarm button to the participant, instruct them to hold it on their hand throughout the session, with the exception of the finger tapping task for which they should leave it on their belly
- [ ] Place participant on the scanner's bed:
  - [ ] Accommodate the head inside the head coil
  - [ ] Check again that it is the 64-channel head coil
  - [ ] Check the scanner's screen that the three coils [SAY MORE SPECIFIC] are connected and active
  - [ ] Solicit feedback on participant’s comfort while positioning them on the scanner bed and suggest ergonomic positioning of arms to avoid discomfort
  - [ ] Make sure the speaker is audible (and not annoying) and confirm the participant's feedback

#### SCAN TIME

**Scan console checklist**

Parameters to double check

  - [ ] MUX: 3
  - [ ] TR: 1490
  - [ ] TE: 3

Console instructions 
  - [ ] 1. Setup of the console
    - [ ] Enter the participant information (surname, name, height and weight)
    - [ ] Select the organ imaged as "brain"
    - [ ] Select the position of the patient as "head first"
    - [ ] Select the protocol

  - [ ] 1. Run localizer
      - [ ] SAVE Rx
      - [ ] SCAN

  - [ ] 1. Prescribe rest  
      - [ ] Select `task-rest_bold` and click once on the localizer image that appears.
      - [ ] Move the block of lines so that the whole brain is covered, with plenty of space in the front and back, top and bottom.
      - [ ] **Do not run yet!**

  - [ ] 1. Run shimming
      - [ ] Select **GE HOS FOV28**
      - [ ] SAVE Rx
      - [ ] SCAN
      - [ ] Adjust circle around the brain so that the red circle goes as tightly around the brain as possible
      - [ ] CALCULATE
      - [ ] **Done**
      - [ ] Select the same scan again
      - [ ] SCAN
      - [ ] Add to Same Series
      - [ ] CALCULATE
          - [ ] If the difference between expected and actual is  < 1 continue; else repeat. 

  - [ ] 1. Fieldmap
      - [ ] Select fmap-fieldmap 
      - [ ] Click the brain once, adjust the prescription so that it covers the whole brain. 
      - [ ] SCAN 

  - [ ] 1. Rest Scan 
      - [ ] Select `task-rest_bold`
      - [ ] Already prescribed from shim setup.  
      - [ ] Put the fixation cross on the bore monitor, check in with the participant:

           > Hey [NAME], we are about to start our first scan run.
           > For this scan, all you have to do is stay still, and look at the screen.
           > Let us know when you’re ready to begin by pressing any button.

      - [ ] PREP SCAN
      - [ ] Physio setup 
          - [ ] Click scan drop down menu 
          - [ ] Research
          - [ ] Phys_flag_record
              - [ ] Change cv to 1
      - [ ] SCAN

  - [ ] 1. Task scans
      - [ ] click start session on the syncbox and run the .es2 using the running man icon
      - [ ] start the sequence on the MR console
      - [ ] Select `task-[TASK NAME]_bold`
      - [ ] Copy prescription from rest (GRx Toolbar -> Select scan to copy from -> Copy) 
      - [ ] SAVE Rx
      - [ ] Put the task window on the bore monitor
          - [ ] check in with the participant.

	           > Hey [NAME], we are about to start our next scan run.
	           > For this scan, [TASK INSTRUCTIONS].
	           > Let us know when you’re ready to begin by pressing any button.

          - [ ] Advance through practice trials, keeping an eye on the participant’s performance on the task if applicable.

      - [ ] PREP SCAN
      - [ ] Physio setup 
          - [ ] Click scan drop down menu 
          - [ ] Research
          - [ ] Phys_flag_record
              - [ ] Change cv to 1
      - [ ] SCAN

  - [ ] 1. Anatomical scans (T1w and T2w)
      - [ ] Prescribe by clicking the localizer image once, and adjust the blue box with crosshairs so that the whole brain is covered, with plenty of space in the front and back, top and bottom.  
      - [ ] SAVE Rx
      - [ ] Put the fixation cross on the bore monitor, check in with the participant:

           > Hey, [NAME], we are about to start our next scan run.
           > For this scan, all you have to do is stay still.
           > Let us know when you’re ready to begin by pressing any button.

      - [ ] SCAN 

**DURING SCAN**

- [ ] Check in with participant frequently
- [ ] Watch for motion if you can see the participant, or use motion monitoring equipment

**AFTER SCAN**

- [ ] Measure and report
  - [ ] The participant's blood pressure with the Omron M3 Comfort device while sitting down 
  - [ ] The participant's body temperature
  - [ ] The scanning room temperature
  - [ ] The scanning room pressure with an MRI-compatible barometer
- [ ] Solicit more feedback on participant’s comfort for future sessions

