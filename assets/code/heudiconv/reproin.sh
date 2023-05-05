#!/bin/bash
heudiconv -s "pilot" -ss "08" -f heuristic_reproin.py -b \
          -o /data/datasets/hcph-pilot/ \
          --files /data/datasets/hcph-pilot/sourcedata/\
                  sub-{{ secrets.ids.pacs_subject | default("01") }}/\
                  ses-{{ secrets.ids.pacs_session | default("18950702") }}/ \
          -l .