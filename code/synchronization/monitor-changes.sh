#!/bin/bash


source activate mydataladenv

cd /home/common/workspace/HCPh-data/Psychopy/

while true; do
    inotifywait -e create,modify -r .
    datalad save -m 'Auto commit from inotify' && datalad push -r --to hos70297-psychopy
done

source deactivate

