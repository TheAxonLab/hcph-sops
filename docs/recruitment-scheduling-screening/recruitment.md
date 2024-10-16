
!!! info "Cohort I"

    Recruitment, screening and informed consent do not apply to Cohort I because the participant is the Principal Investigator himself.

!!! info "Cohort III"

    Recruitment, screening and informed consent do not apply to Cohort III because the sessions have already been acquired.

## Recruitment shortlist

- [ ] Distribute the [recruitment flyers](../assets/files/flyer_FR.pdf) at CHUV, as well as on EPFL and UNIL campuses, both physically and electronically (e.g., e-mail lists).
- [ ] Insert any new potential participant who shows interest by calling :fontawesome-solid-square-phone: {{ secrets.phones.study | default("###-###-####") }}, SMS, email, etc. in [our recruits spreadsheet]({{ secrets.data.recruits_url | default("/redacted.html") }}). Make sure you get **an e-mail contact** to send documents.

!!!warning "Recruits shortlist"

    - [ ] Remove all flyers and indicate that recruitment is not open anymore once the shortlist quotas have been reached (5 males and 5 females for Cohort II).

## First contact

!!!warning "Important"
    
    - [ ] Write an email to them within **the next 24h**.
    - [ ] Use [the email template](#first-contact-email-fr) and make sure you attach the MRI Safety and Screening Questionnaire and the Informed Consent Form.
    - [ ] Confirm the reception of the email AND the documents over the phone.

## Phone call

!!!info

    The study coordinator ({{ secrets.people.study_coordinator | default("███") }}, Assistante doctorante) will call the potential participant **after at least three days** of having sent the information in the case of cohort II ([HRA, art. 16-3][1]).

- [ ] Use the [phone script](#first-contact-call-fr) to drive the conversation and record participant responses to questions.
- [ ] If participant consents to the phone screen, conduct it and mark the results (screener date, if responded "yes" to any medical questions, whether or not passed screener) in the appropriate columns of the recruitment spreadsheet.
- [ ] Confirm whether the potential participant understood the MRI Safety & Screening Questionnaire, and discuss with them any questions or potential reasons that may disqualify them to participate.

!!!danger "Carefully screen the subject"
    - [ ] In case of any doubts emerging from the MRI safety screening, indicate the potential participant that you will call them back **within three days**, after contacting the responsible physician.
    - [ ] Collect as much information as possible about their case.
    - [ ] Contact {{ secrets.people.medical_contact | default("███") }} with all the information.
    - [ ] In case of negative assessment by the medical contact, the volunteer **MUST NOT** participate in the study.
    - [ ] Otherwise, call back the participant as soon as possible to confirm participation.

- [ ] Female participants will be informed and must acknowledge that they must take a pregnancy test before the first scanning session.
- [ ] If the candidate participant does not pass the phone screen, then end the interview, informing them that they do not meet our inclusion criteria, and mark the screen fail in the recruitment spreadsheet.
- [ ] Make sure that the participant's questions about the study are all addressed and answered.
- [ ] Request the potential participant to confirm they are willing to continue.
    - [ ] Indicate in the shortlist of recruits that the participant is ready to schedule the first session.
    - [ ] Tell the participant that they will be called back to set up the first session.
    - [ ] Remind them that they can ask further questions at any time before the MRI scan session.

## Templates

### First contact email (FR)

!!! warning "Remember to attach the MRI Safety and Screening Questionnaire and the ICF."

{% include 'boiler/script-invitation-fr.md' %}

### First contact call (FR)

{% include 'boiler/script-call-fr.md' %}

[1]: https://www.fedlex.admin.ch/eli/cc/2013/642/en "The Swiss Federal Council, Federal Act of 30 September 2011 on Research involving Human Beings (Human Research Act, HRA). 2011. Accessed: Nov. 29, 2021."
