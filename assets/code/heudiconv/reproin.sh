#!/bin/bash
heudiconv -s "pilot" -ss "08" -f heuristic_reproin.py -b \
          -o /data/datasets/hcph-pilot/ \
          --files /data/datasets/hcph-pilot/sourcedata/\
                  sub-{{ secrets.ids.pacs_subject }}/\
                  ses-{{ secrets.ids.pacs_session }}/ \
          -l .