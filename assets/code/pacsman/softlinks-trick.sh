sesid=1
for session in $( find {{ settings.paths.pilot_sourcedata }}/sub-{{ secrets.ids.pacs_subject | default("01") }}/ -maxdepth 1 -type d -name "ses-*" | sort ); do 
        cmd="ln -s $session $PWD/ses-pilot$( printf '%03d' $sesid )"
        echo $cmd
        eval $cmd
        sesid=$((sesid+1))
done