#!/bin/bash
heudiconv -s "001" -ss "pilot001" -b -l . -o /data/datasets/hcph/ \
          -f {{ secrets.data.sops_clone_path | default('<sops_clone_path>') }}/code/heudiconv/reproin.py \
          --files /data/datasets/hcph-pilot-sourcedata/\
                  sub-{{ secrets.ids.pacs_subject | default("01") }}/\
                  ses-{{ secrets.ids.pacs_session | default("18950702") }}/
