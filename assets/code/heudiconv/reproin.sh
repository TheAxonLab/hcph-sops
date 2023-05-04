#!/bin/bash
heudiconv -s "pilot" -ss "08" -f heuristic_reproin.py -b \
          -o /data/datasets/hcph-pilot/ \
          --files /data/datasets/hcph-pilot/sourcedata/\
                  sub-2022_11_07_15_37_06_STD_1_3_12_2_1107_5_99_3/\
                  ses-20230315163232/ \
          -l .