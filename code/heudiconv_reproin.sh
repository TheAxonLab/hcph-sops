heudiconv -s "pilot" -ss "08" -f heuristic_ReproIn.py -b -o /data/datasets/hcph-pilot/ --files /data/datasets/hcph-pilot/sourcedata/sub-2022_11_07_15_37_06_STD_1_3_12_2_1107_5_99_3/ses-20230315163232/ -l .
#docker run --user=$(id -u):$(id -g) -e "UID=$(id -u)" -e "GID=$(id -g)" --rm -t -v /data/datasets/hcph-pilot/sourcedata/sub-2022_11_07_15_37_06_STD_1_3_12_2_1107_5_99_3/ses-20230315163232/:/input:ro -v /data/datasets/hcph-pilot/:/output  nipy/heudiconv:0.12.2 -s "pilot" -ss "008" -f reproin -b -o /output --files /input -l .
