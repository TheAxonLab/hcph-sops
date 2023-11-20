from eyetrackingrun import EyeTrackingRun
import argparse
import pandas as pd
import os
from pyedfread import edf


def main():
    parser = argparse.ArgumentParser(description="Eye Tracking Library CLI")
    parser.add_argument("--DATA_PATH", type=str, help="Path to input data")
    parser.add_argument("--BIDS_PATH", type=str, help="Path to BIDS dataset")
    parser.add_argument(
        "--schedule_file",
        type=str,
        default="",
        help="Path to schedule file (default is an empty string)",
    )
    parser.add_argument(
        "--EDF_file_name",
        type=str,
        default="",
        help="Optional EDF file name (default is an empty string)",
    )
    parser.add_argument("--participant", type=int, default=9999, help="Participant ID")
    parser.add_argument("--session", type=int, default=9999, help="Session ID")
    parser.add_argument("--task_name", type=str, help="Task name")
    parser.add_argument(
        "--pe", type=str, default="", help="phase encoding direction (optional)"
    )
    parser.add_argument(
        "--screen_resolution",
        type=int,
        nargs=2,
        help="Screen resolution as two integers",
    )
    parser.add_argument(
        "--message_first_trigger",
        type=str,
        default="",
        help="Message first trigger (default is an empty string)",
    )
    parser.add_argument("--save_plots", type=bool, default=False, help="Save plots")
    parser.add_argument(
        "--path_plot_save", type=str, default="", help="Path to save plots"
    )
    parser.add_argument(
        "--ETinfo_json_path",
        type=str,
        default="info_ET.json",
        help="Path to the JSON file containing ET specifications",
    )
    args = parser.parse_args()

    if args.schedule_file:
        edf_lookup = pd.read_csv(args.schedule_file, sep="\t", na_values="n/a")
        et_session = edf_lookup.query(f"session == {args.session}")

        if not et_session.empty:
            EDF_file_name = os.path.join(
                args.DATA_PATH, et_session[f"{args.task_name}_edf"].values[0]
            )
            pe = et_session.PE.values[0]
            samples, events, messages = edf.pread(EDF_file_name, trial_marker=b"")
        else:
            print(f"No matching entry in the schedule file for session {args.session}")
            return
    else:
        if args.EDF_file_name:
            EDF_file_name = os.path.join(args.DATA_PATH, args.EDF_file_name)
            samples, events, messages = edf.pread(EDF_file_name, trial_marker=b"")
            pe = args.pe
        else:
            print("Provide a file name or the path to a schedule file.")
            return

    et_run = EyeTrackingRun(
        session=args.session,
        task_name=args.task_name,
        participant=args.participant,
        samples=samples,
        events=events,
        messages=messages,
        message_first_trigger=args.message_first_trigger,
        screen_resolution=tuple(args.screen_resolution),
        pe=pe,
    )
    if args.save_plots == True:
        et_run.plot_pupil_size(notebook=False, save=True, path_save=args.path_plot_save)
        et_run.plot_delta(notebook=False, save=True, path_save=args.path_plot_save)
        et_run.plot_coordinates_ts(
            notebook=False, save=True, path_save=args.path_plot_save
        )
        et_run.plot_heatmap_coordinate_density(
            notebook=False, save=True, path_save=args.path_plot_save
        )

    et_run.save_and_process_samples(args.BIDS_PATH, include_events=True)
    et_run.create_info_json(args.BIDS_PATH, args.ETinfo_json_path)


if __name__ == "__main__":
    main()
