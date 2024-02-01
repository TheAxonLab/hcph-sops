## Reading EyeLink's EDF recordings

Our ET device produces EyeLink's EDF recording files, which will be accessed with [*PyEDFRead*](https://github.com/oesteban/pyedfread).

??? tip "*PyEDFRead* must be installed"

    Make sure *PyEDFRead* is installed on the computer where conversion will be executed, as described in [the software annex](../data-collection/notes-software.md#conversion-of-et-recordings-into-bids).

- [ ] Open a run's EDF file:

    ``` Python
    from pyedfread import edf

    recording, events, messages = edf.pread(str(DATA_PATH / "example-run.edf"), trial_marker=b"")
    ```

    As a result, thre *Pandas*' dataframes will be obtained:

    * `recording` contains the actual ET data,
    * `events` contains information of events reported by the device (most substantially these are fixations, saccades, and blinks), and
    * `messages` with the logged textual messages sent to the device.

## Processing the *Pandas* dataframes generated by *PyEDFRead*

The code snippets are derived from the [`EyeTrackingRun` object](../assets/code/eyetracking/eyetrackingrun.py).

!!! warning "Disclamer: despite this code attempting to be general, some parts focus on single-eye recordings"

### Parsing the `messages` dataframe

First, we clean the `messages` dataframe, as it may have headers ending with space and drop duplicate rows:

``` Python
messages = messages.rename(
    columns={c: c.strip() for c in messages.columns.values}
).drop_duplicates()
```

**Extract and reserve calibration messages**.
EyeLink reports the calibration information as messages, which are marked up with a `!CAL` prefix.
We extract them into a separate variable to process them at a later time:

```Python
# Extract calibration headers
_cal_hdr = messages.trialid.str.startswith("!CAL")
calibration = messages[_cal_hdr]
messages = messages.drop(messages.index[_cal_hdr])
```

**Extracting the `StartTime` and `StopTime` metadata**.
We then search for messages signaling the start and stop run events.
These events are stored in the JSON sidecar file annotating our `_eyetrack.tsv.gz` file.
In our *Psychopy* experiment files, we configure messages be sent to the ET at these events.
The message changes a little with the RSfMRI experiment, but are usually like `hello <taskname>` and `bye <taskname>`, which are stored in the variables `message_first_trigger` and `message_last_trigger` variables, respectively.
In the last line, we clean up these used-up lines from the dataframe.

``` Python
# Find Start time
start_rows = messages.trialid.str.contains(
    message_first_trigger, case=False, regex=True
)
stop_rows = messages.trialid.str.contains(
    message_last_trigger, case=False, regex=True
)

# Extract calibration headers
_cal_hdr = messages.trialid.str.startswith("!CAL")
calibration = messages[_cal_hdr]
messages = messages.drop(messages.index[_cal_hdr])

# Pick the LAST of the start messages
metadata["StartTime"] = (
    int(messages[start_rows].trialid_time.values[-1])
    if start_rows.any()
    else None
)

# Pick the FIRST of the stop messages
metadata["StopTime"] = (
    int(messages[stop_rows].trialid_time.values[0])
    if stop_rows.any()
    else None
)

# Drop start and stop messages from messages dataframe
messages = messages.loc[~start_rows & ~stop_rows, :]
```

**Extracting basic metadata**.
Next, we extract basic metadata: the eye being sampled, the ET approach, and the sampling frequency.
These are parsed from the following message:

```
!MODE RECORD CR 1000 2 0 R
```

``` Python
mode_record = messages.trialid.str.startswith("!MODE RECORD")

meta_record = {
    "freq": DEFAULT_FREQUENCY,
    "mode": DEFAULT_MODE,
    "eye": DEFAULT_EYE,
}

if mode_record.any():
    try:
        meta_record = re.match(
            r"\!MODE RECORD (?P<mode>\w+) (?P<freq>\d+) \d \d (?P<eye>[RL]+)",
            messages[mode_record].trialid.iloc[-1].strip(),
        ).groupdict()

        meta_record["eye"] = EYE_CODE_MAP[meta_record["eye"]]
        meta_record["mode"] = (
            "P-CR" if meta_record["mode"] == "CR" else meta_record["mode"]
        )
    except AttributeError:
        warn(
            "Error extracting !MODE RECORD message, "
            "using default frequency, mode, and eye"
        )
    finally:
        messages = messages.loc[~mode_record]

eye = (
    ("right", "left") if meta_record["eye"] == "both" else (meta_record["eye"],)
)

metadata["SamplingFrequency"] = int(meta_record["freq"])
metadata["EyeTrackingMethod"] = meta_record["mode"]
metadata["RecordedEye"] = meta_record["eye"]
```

**Extracting screen parameters**.
We then parse the `GAZE_COORDS` message, with format `GAZE_COORDS 0.00 0.00 800.00 600.00`:

```Python
# Extract GAZE_COORDS message signaling start of recording
gaze_msg = messages.trialid.str.startswith("GAZE_COORDS")

metadata["ScreenAOIDefinition"] = [
    "square",
    DEFAULT_SCREEN,
]
if gaze_msg.any():
    try:
        gaze_record = re.match(
            r"GAZE_COORDS (\d+\.\d+) (\d+\.\d+) (\d+\.\d+) (\d+\.\d+)",
            messages[gaze_msg].trialid.iloc[-1].strip(),
        ).groups()
        metadata["ScreenAOIDefinition"][1] = [
            int(round(float(gaze_record[0]))),
            int(round(float(gaze_record[2]))),
            int(round(float(gaze_record[1]))),
            int(round(float(gaze_record[3]))),
        ]
    except AttributeError:
        warn("Error extracting GAZE_COORDS")
    finally:
        messages = messages.loc[~gaze_msg]
```

**Extracting parameters of the pupil fit model**.
Next, we look into messages containing `ELCL_PROC` and `ELCL_EFIT_PARAMS`, which specify the pupil fit.
The format of these messages is as follows:

```
ELCL_PROC ELLIPSE (5)
ELCL_EFIT_PARAMS 1.01 4.00  0.15 0.05  0.65 0.65  0.00 0.00 0.30
```

```Python
    # Extract ELCL_PROC AND ELCL_EFIT_PARAMS to extract pupil fit method
    pupilfit_msg = messages.trialid.str.startswith("ELCL_PROC")

    if pupilfit_msg.any():
        try:
            pupilfit_method = [
                val
                for val in messages[pupilfit_msg]
                .trialid.iloc[-1]
                .strip()
                .split(" ")[1:]
                if val
            ]
            metadata["PupilFitMethod"] = pupilfit_method[0].lower()
            metadata["PupilFitMethodNumberOfParameters"] = int(
                pupilfit_method[1].strip("(").strip(")")
            )
        except AttributeError:
            warn("Error extracting ELCL_PROC (pupil fitting method)")
        finally:
            messages = messages.loc[~pupilfit_msg]

    pupilfit_msg_params = messages.trialid.str.startswith("ELCL_EFIT_PARAMS")
    if pupilfit_msg_params.any():
        rows = messages[pupilfit_msg_params]
        row = rows.trialid.values[-1].strip().split(" ")[1:]
        try:
            metadata["PupilFitParameters"] = [
                tuple(float(val) for val in vals)
                for k, vals in groupby(row, key=bool)
                if k
            ]
        except AttributeError:
            warn("Error extracting ELCL_EFIT_PARAMS (pupil fitting parameters)")
        finally:
            messages = messages.loc[~pupilfit_msg_params]
```

**Calibration validation**.
If calibration was performed, most likely a validation procedure was executed next.
These messages take the format `VALIDATE R 4POINT 4 RIGHT  at 752,300  OFFSET 0.35 deg.  -8.7,-3.8 pix.`

```Python
# Extract VALIDATE messages for a calibration validation
validation_msg = messages.trialid.str.startswith("VALIDATE")

if validation_msg.any():
    metadata["ValidationPosition"] = []
    metadata["ValidationErrors"] = []

for i_row, validate_row in enumerate(messages[validation_msg].trialid.values):
    prefix, suffix = validate_row.split("OFFSET")
    validation_eye = (
        f"eye{eye.index('right') + 1}"
        if "RIGHT" in prefix
        else f"eye{eye.index('left') + 1}"
    )
    validation_coords = [
        int(val.strip())
        for val in prefix.rsplit("at", 1)[-1].split(",")
        if val.strip()
    ]
    metadata["ValidationPosition"].append(
        [validation_eye, validation_coords]
    )

    validate_values = [
        float(val)
        for val in re.match(
            r"(-?\d+\.\d+) deg\.\s+(-?\d+\.\d+),(-?\d+\.\d+) pix\.",
            suffix.strip(),
        ).groups()
    ]

    metadata["ValidationErrors"].append(
        (validation_eye, validate_values[0], tuple(validate_values[1:]))
    )
messages = messages.loc[~validation_msg]
```

**Extracting final bits of metadata**.
Finally, we parse the last of the `THRESHOLDS` messages.

```Python
# Extract THRESHOLDS messages prior recording and process last
thresholds_msg = messages.trialid.str.startswith("THRESHOLDS")
if thresholds_msg.any():
    metadata["PupilThreshold"] = [None] * len(eye)
    metadata["CornealReflectionThreshold"] = [None] * len(eye)
    thresholds_chunks = (
        messages[thresholds_msg].trialid.iloc[-1].strip().split(" ")[1:]
    )
    eye_index = eye.index(EYE_CODE_MAP[thresholds_chunks[0]])
    metadata["PupilThreshold"][eye_index] = int(thresholds_chunks[-2])
    metadata["CornealReflectionThreshold"][eye_index] = int(
        thresholds_chunks[-1]
    )
messages = messages.loc[~thresholds_msg]
```

**Flush the remaining messages as a metadata entry**.
In order to preserve all the information generated by the ET for further use, we dump the remainder of the messages dataframe into a metadata key `LoggedMessages`:

```Python
# Consume the remainder of messages
if not messages.empty:
    metadata["LoggedMessages"] = [
        (int(msg_timestamp), msg.strip())
        for msg_timestamp, msg in messages[["trialid_time", "trialid"]].values
    ]
```

### Parsing the `recording` dataframe

**Curation of the input dataframe**.
The `recording` dataframe will have several issues that we want to resolve from the beginning.
These includes bugs and inconsistencies in some of the column names, dropping data with timestamp set to zero, implausible values, empty columns, etc.

```Python
# Normalize timestamps (should be int and strictly positive)
recording = recording.astype({"time": int})
recording = recording[recording["time"] > 0]

recording = recording.rename(
    columns={
        # Fix buggy header names generated by pyedfread
        "fhxyvel": "fhxvel",
        "frxyvel": "frxvel",
        # Normalize weird header names generated by pyedfread
        "rx": "screen_ppdeg_x_coordinate",
        "ry": "screen_ppdeg_y_coordinate",
        # Convert some BIDS columns
        "time": "timestamp",
    }
)

# Split extra columns from the dataframe
extra = recording[["flags", "input", "htype"]]
recording = recording.drop(columns=["flags", "input", "htype"])

# Remove columns that are always very close to zero
recording = recording.loc[:, (recording.abs() > 1e-8).any(axis=0)]
# Remove columns that are always 1e8 or more
recording = recording.loc[:, (recording.abs() < 1e8).any(axis=0)]
# Replace unreasonably high values with NaNs
recording = recording.replace({1e8: np.nan})
```

**Remove columns that do not apply (e.g., only one eye recorded)**.
Next, we clean up unnecessary columns.

```Python
# Drop one eye's columns if not interested in "both"
if remove_eye := set(("left", "right")) - set(eye):
    remove_eye = remove_eye.pop()  # Drop set decoration
    recording = recording.reindex(
        columns=[c for c in recording.columns if remove_eye not in c]
    )
```

**Clean-up pupil size and gaze position**.
These are the parameters we most likely we care for, so special curation is applied:

``` Python
# Drop one eye's columns if not interested in "both"
if remove_eye := set(("left", "right")) - set(eye):
    remove_eye = remove_eye.pop()  # Drop set decoration
    recording = recording.reindex(
        columns=[c for c in recording.columns if remove_eye not in c]
    )

for eyenum, eyename in enumerate(eye):
    # Clean-up implausible values for pupil area (pa)
    recording.loc[
        recording[f"pa_{eyename}"] < 1, f"pa_{eyename}"
    ] = np.nan
    recording = recording.rename(
        columns={f"pa_{eyename}": f"eye{eyenum + 1}_pupil_size"}
    )

    # Clean-up implausible values for gaze x position
    recording.loc[
        (recording[f"gx_{eyename}"] < 0)
        | (recording[f"gx_{eyename}"] > screen_resolution[0]),
        f"gx_{eyename}",
    ] = np.nan
    # Clean-up implausible values for gaze y position
    recording.loc[
        (recording[f"gy_{eyename}"] <= 0)
        | (recording[f"gy_{eyename}"] > screen_resolution[1]),
        f"gy_{eyename}",
    ] = np.nan
```

**Munging columns to comply with BIDS**.
At this point, the dataframe is almost ready for writing out as BIDS.

``` Python
# Interpolate BIDS column names
columns = list(
    set(recording.columns)
    - set(
        (
            "timestamp",
            "screen_ppdeg_x_coordinate",
            "screen_ppdeg_y_coordinate",
            "eye1_pupil_size",
            "eye2_pupil_size",
        )
    )
)
bids_columns = []
for eyenum, eyename in enumerate(eye):
    for name in columns:
        colprefix = f"eye{eyenum + 1}" if name.endswith(f"_{eyename}") else ""
        _newname = name.split("_")[0]
        _newname = re.sub(r"([xy])$", r"_\1_coordinate", _newname)
        _newname = re.sub(r"([xy])vel$", r"_\1_velocity", _newname)
        _newname = _newname.split("_", 1)
        _newname[0] = EDF2BIDS_COLUMNS[_newname[0]]
        _newname.insert(0, colprefix)
        bids_columns.append("_".join((_n for _n in _newname if _n)))

# Rename columns to be BIDS-compliant
recording = recording.rename(columns=dict(zip(columns, bids_columns)))

# Reorder columns to render nicely (tracking first, pupil size after)
columns = sorted(
    set(recording.columns.values).intersection(BIDS_COLUMNS_ORDER),
    key=lambda entry: BIDS_COLUMNS_ORDER.index(entry),
)
columns += [c for c in recording.columns.values if c not in columns]
recording = recording.reindex(columns=columns)
```

### Parsing the calibration messages

We had reserved the calibration information for extraction of metadata.
In the case of our ET, the calibration information is textual and as follows:

```
!CAL
>>>>>>> CALIBRATION (HV9,P-CR) FOR RIGHT: <<<<<<<<<

!CAL Calibration points:

!CAL -18.8, -42.0         0,      0

!CAL -16.8, -58.4         0,  -2457

!CAL -20.0, -25.9         0,   2457

!CAL -45.1, -42.6     -3474,      0

!CAL  10.2, -40.9      3474,      0

!CAL -45.4, -59.0     -3474,  -2457

!CAL  11.1, -55.5      3474,  -2457

!CAL -47.5, -27.1     -3474,   2457

!CAL  8.6, -25.6      3474,   2457

!CAL eye check box: (L,R,T,B)
      -53    17   -62   -22


!CAL href cal range: (L,R,T,B)
    -5211  5211 -3686  3686


!CAL Cal coeff:(X=a+bx+cy+dxx+eyy,Y=f+gx+goaly+ixx+jyy)
   5.882e-05  125.7  12.521 -0.22744 -0.18622
   4.4115e-05 -4.6332  150.8 -0.048749  0.093667


!CAL Prenormalize: offx, offy = -18.822 -42.021


!CAL Quadrant center: centx, centy =
   5.882e-05  4.4115e-05


!CAL Corner correction:
   3.207e-05, -1.7627e-06
  -1.6438e-05,  3.5065e-05
  -2.0184e-05, -1.0586e-05
   5.7616e-06,  1.5672e-05


!CAL Gains: cx:120.898 lx:115.734 rx:103.799

!CAL Gains: cy:164.746 ty:163.045 by:164.277

!CAL Resolution (upd) at screen center: X=2.2, Y=1.6

!CAL Gain Change Proportion: X: 0.115 Y: 0.008

!CAL Gain Ratio (Gy/Gx) = 1.363

!CAL Cross-Gain Ratios: X=0.100, Y=0.031

!CAL Quadrant fixup[0] = 0.059,0.003

!CAL Quadrant fixup[1] = 0.029,0.062

!CAL Quadrant fixup[2] = 0.037,0.019

!CAL Quadrant fixup[3] = 0.010,0.027

!CAL PCR gain ratio(x,y) = 2.442, 1.946

!CAL CR gain match(x,y) = 1.020, 1.020

!CAL Slip rotation correction OFF

!CAL CALIBRATION HV9 R RIGHT   GOOD

!CAL VALIDATION HV9 R RIGHT GOOD ERROR 0.49 avg. 0.92 max  OFFSET 0.17 deg. -2.4,-3.7 pix.
```

The `!CAL` messages are parsed as follows:

```Python
# Parse calibration metadata
metadata["CalibrationCount"] = 0
if not calibration.empty:
    warn("Calibration of more than one eye is not implemented")
    calibration.trialid = calibration.trialid.str.replace("!CAL", "")
    calibration.trialid = calibration.trialid.str.strip()

    metadata["CalibrationLog"] = list(
        zip(
            calibration.trialid_time.values.astype(int),
            calibration.trialid.values,
        )
    )

    calibrations_msg = calibration.trialid.str.startswith(
        "VALIDATION"
    ) & calibration.trialid.str.contains("ERROR")
    metadata["CalibrationCount"] = calibrations_msg.sum()

    calibration_last = calibration.index[calibrations_msg][-1]
    try:
        meta_calib = re.match(
            r"VALIDATION (?P<ctype>[\w\d]+) (?P<eyeid>[RL]+) (?P<eye>RIGHT|LEFT) "
            r"(?P<result>\w+) ERROR (?P<avg>-?\d+\.\d+) avg\. (?P<max>-?\d+\.\d+) max\s+"
            r"OFFSET (?P<offsetdeg>-?\d+\.\d+) deg\. "
            r"(?P<offsetxpix>-?\d+\.\d+),(?P<offsetypix>-?\d+\.\d+) pix\.",
            calibration.loc[calibration_last, "trialid"].strip(),
        ).groupdict()

        metadata["CalibrationType"] = meta_calib["ctype"]
        metadata["AverageCalibrationError"] = [float(meta_calib["avg"])]
        metadata["MaximalCalibrationError"] = [float(meta_calib["max"])]
        metadata["CalibrationResultQuality"] = [meta_calib["result"]]
        metadata["CalibrationResultOffset"] = [
            float(meta_calib["offsetdeg"]),
            (float(meta_calib["offsetxpix"]), float(meta_calib["offsetypix"])),
        ]
        metadata["CalibrationResultOffsetUnits"] = ["deg", "pixels"]
    except AttributeError:
        warn("Calibration data found but unsuccessfully parsed for results")
```

### Parsing the ``events`` dataframe

The events dataframe contains several parameters calculated by the EyeLink software.
It is important to remark that these *events* are not exactly the same as the experimental *events* that are encoded in the dataset.
These *events* are specific to the recording of ET data with the EyeLink device.

```Python
# Process events: first generate empty columns
recording["eye1_fixation"] = 0
recording["eye1_saccade"] = 0
recording["eye1_blink"] = 0

# Add fixations
for _, fixation_event in events[
    events["type"] == "fixation"
].iterrows():
    recording.loc[
        (recording["timestamp"] >= fixation_event["start"])
        & (recording["timestamp"] <= fixation_event["end"]),
        "eye1_fixation",
    ] = 1

# Add saccades, and blinks, which are a sub-event of saccades
for _, saccade_event in events[
    events["type"] == "saccade"
].iterrows():
    recording.loc[
        (recording["timestamp"] >= saccade_event["start"])
        & (recording["timestamp"] <= saccade_event["end"]),
        "eye1_saccade",
    ] = 1

    if saccade_event["blink"] == 1:
        recording.loc[
            (recording["timestamp"] >= saccade_event["start"])
            & (recording["timestamp"] <= saccade_event["end"]),
            "eye1_blink",
        ] = 1
```

## Writing the data into the BIDS structure

Finally, data can be written out if the reference run corresponding to the ET recording is provided:

```Python

def write_bids(
    et_run: EyeTrackingRun,
    exp_run: str | Path,
) -> List[str]:
    """
    Save an eye-tracking run into a existing BIDS structure.

    Parameters
    ----------
    et_run : :obj:`EyeTrackingRun`
        An object representing an eye-tracking run.
    exp_run : :obj:`os.pathlike`
        The path of the corresponding neuroimaging experiment in BIDS.

    Returns
    -------
    List[str]
        A list of generated files.

    """

    exp_run = Path(exp_run)
    out_dir = exp_run.parent
    refname = exp_run.name
    extension = "".join(exp_run.suffixes)
    suffix = refname.replace(extension, "").rsplit("_", 1)[-1]
    refname = refname.replace(f"_{suffix}", "_eyetrack")

    # Remove undesired entities
    refname = re.sub(r"_part-(mag|phase)", "", refname)
    refname = re.sub(r"_echo-[\w\d]+", "", refname)

    # Write out sidecar JSON
    out_json = out_dir / refname.replace(extension, ".json")
    out_json.write_text(
        json.dumps(et_run.metadata, sort_keys=True, indent=2)
    )

    # Write out data
    out_tsvgz = out_dir / refname.replace(extension, ".tsv.gz")
    et_run.recording.to_csv(
        out_tsvgz,
        sep="\t",
        index=False,
        header=False,
        compression="gzip",
        na_rep="n/a",
    )

    return str(out_tsvgz), str(out_json)
```