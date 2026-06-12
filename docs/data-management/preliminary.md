!!! danger "*DataLad* must be version 1.0 or later"

This project maintains data under version control thanks to *DataLad*<sup>[1]</sup>.
For instructions on how to setup *DataLad* on your PC, please refer to the [official documentation](https://handbook.datalad.org/en/latest/intro/installation.html).
When employing high-performance computing (HPC), we provide [some specific guidelines](../processing/environment.md).

!!! important "Please read the [*DataLad Handbook*](https://handbook.datalad.org/en/latest/index.html), especially if you are new to this tool"

## Creating a *DataLad* dataset

- [ ] Designate a host and folder where data will be centralized.
    In the context of this study, the primary copy of data will be downloaded into {{ secrets.hosts.oesteban | default('&lt;hostname&gt;') }}, under the path `{{ settings.paths.pilot_sourcedata }}` for the piloting acquisitions and `{{ settings.paths.sourcedata }}` for the experimental data collection.
- [ ] Install the `bids` *DataLad procedure* provided from this repository to facilitate the correct intake of data and metadata:

    ``` shell
    PYTHON_SITE_PACKAGES=$( python -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])' )
    ln -s {{ secrets.data.sops_clone_path | default('<path>') }}/code/datalad/cfg_bids.py ${PYTHON_SITE_PACKAGES}/datalad/resources/procedures/
    ```

    ??? bug "*DataLad*'s documentation does not recommend this approach"

        For safety, you can prefer to use *DataLad*'s recommendations and place the `cfg_bids.py` file in some of the suggested paths.

- [ ] Check the new *procedure* is available as `bids`:

    ``` {.shell hl_lines="2"}
    $ datalad run-procedure --discover
    cfg_bids (/home/oesteban/.miniconda/lib/python3.9/site-packages/datalad/resources/procedures/cfg_bids.py) [python_script]
    cfg_yoda (/home/oesteban/.miniconda/lib/python3.9/site-packages/datalad/resources/procedures/cfg_yoda.py) [python_script]
    cfg_metadatatypes (/home/oesteban/.miniconda/lib/python3.9/site-packages/datalad/resources/procedures/cfg_metadatatypes.py) [python_script]
    cfg_text2git (/home/oesteban/.miniconda/lib/python3.9/site-packages/datalad/resources/procedures/cfg_text2git.py) [python_script]
    cfg_noannex (/home/oesteban/.miniconda/lib/python3.9/site-packages/datalad/resources/procedures/cfg_noannex.py) [python_script]
    ```

    !!! tip "Learn more about the [YODA principles (*DataLad Handbook*)](https://handbook.datalad.org/en/latest/basics/101-127-yoda.html)"

- [ ] Create a *DataLad* dataset for the original dataset:

    ``` shell
    cd /data/datasets/
    datalad create -c bids hcph-dataset
    ```
<!--
- [ ] Create a *DataLad* subdataset called `sourcedata`

    ``` bash title="bash oneliner to link sessions"
{% filter indent(width=4) %}
{% include 'code/pacsman/softlinks-trick.sh' %}
{% endfilter %}
    ```
-->

- [ ] Configure a [RIA store](https://handbook.datalad.org/en/latest/beyond_basics/101-147-riastores.html), where large files will be pushed (and pulled from when installing the dataset in other computers)
    ``` shell title="Creating a RIA sibling to store large files"
    cd hcph-dataset
    datalad create-sibling-ria -s ria-storage --alias hcph-dataset \
            --new-store-ok --storage-sibling=only \
            "ria+ssh://{{ secrets.login.curnagl_ria | default('<username>') }}@curnagl.dcsr.unil.ch:{{ secrets.data.curnagl_ria_store_data | default('<absolute-path-of-store>') }}"
    ```

    ??? bug "Getting `[ERROR ] 'SSHRemoteIO' ...`"

        If you encounter:

        ```Text
        [ERROR ] 'SSHRemoteIO' object has no attribute 'url2transport_path'
        ```

        Type in the following *Git* configuration ([datalad/datalad-next#754](https://github.com/datalad/datalad-next/issues/754)):

        ```Bash
        git config --global --add datalad.extensions.load next
        ```

- [ ] Configure a [GitHub sibling](https://handbook.datalad.org/en/0.15/basics/101-139-hostingservices.html), to host the Git history and the annex metadata:
    ``` shell title="Creating a GitHub sibling to store DataLad's infrastructure and dataset's metadata"
    datalad siblings add --dataset . --name github \
            --pushurl git@github.com:{{ secrets.data.gh_repo | default('<organization>/<repo_name>') }}.git \
            --url https://github.com/{{ secrets.data.gh_repo | default('<organization>/<repo_name>') }}.git \
            --publish-depends ria-storage
    ```

## Synchronizing your *DataLad* dataset

Once the dataset is installed, new sessions will be added as data collection goes on.
When a new session is added, your *DataLad* dataset will remain at the same point in history (meaning, it will become out-of-date).

- [ ] Pull new changes in the git history.
    *DataLad* will first fetch Git remotes and merge for you.

    ``` shell
    cd hcph-dataset/  # <--- cd into the dataset's path
    datalad update -r --how ff-only
    ```

- [ ] If you need the data, now you can get the data as usual:

    ``` shell
    find sub-001/ses-pilot019 -name "*.nii.gz" | xargs datalad get -J 8
    ```

### Adding data or metadata

- [ ] Use `datalad save` indicating the paths you want to add, and include `--to-git` if the file contains only metadata (e.g., JSON files).

    === "Adding data files (e.g., NIfTI and compressed TSV files)"

        ``` shell
        find sub-001/ses-pilot019 -name "*.nii" -or -name "*.nii.gz" -or -name "*.tsv.gz" | \
            xargs datalad save -m '"add(pilot019): new session data (NIfTI and compressed TSV)"'
        ```

    === "Adding metadata files"

        ``` shell
        find sub-001/ses-pilot019 -name "*.json" -or -name "*.tsv" -or -name "*.bvec" -or -name "*.bval" | \
            xargs datalad save -m --to-git '"add(pilot019): new session metadata (JSON, TSV, bvec/bval)"'
        ```

## Preparing derivative subdatasets

*Datalad*'s datasets modularity can be leveraged with derivatives.
Instead of creating a monolithic and large dataset for all derivatives, we will create datasets for each of the derivatives and then aggregate them as subdatasets.
The steps to create derivative subdatasets is similar to those of the original dataset.
To make this documentation generalize across different derivative sets, we will first set a variable with the derivative set name.
In this case, the steps are demonstrated for the outputs of *sMRIPrep*.

- [ ] Initiate the derivative dataset:
    ```Bash
    export DERIVS_REPO=smriprep
    datalad create -c bids hcph-${DERIVS_REPO}
    cd hcph-${DERIVS_REPO}
    ```

- [ ] Create the RIA store:
    ``` shell title="Creating a RIA sibling to store large files"
    datalad create-sibling-ria -s ria-storage --alias hcph-${DERIVS_REPO} \
            --new-store-ok --storage-sibling=only \
            "ria+ssh://{{ secrets.login.curnagl_ria | default('<username>') }}@curnagl.dcsr.unil.ch:{{ secrets.data.curnagl_ria_store_derivs | default('<absolute-path-of-store>') }}"
    ```

    ??? bug "Getting `[ERROR ] 'SSHRemoteIO' ...`"

        If you encounter:

        ```Text
        [ERROR ] 'SSHRemoteIO' object has no attribute 'url2transport_path'
        ```

        Type in the following *Git* configuration ([datalad/datalad-next#754](https://github.com/datalad/datalad-next/issues/754)):

        ```Bash
        git config --global --add datalad.extensions.load next
        ```

- [ ] Configure the GitHub sibling:

    === "When the GitHub repo doesn't exist yet"

        ``` shell
        datalad create-sibling-github --dataset . -s github --existing error \
                --access-protocol https-ssh --private \
                --description "HCPh Derivatives: ${DERIVS_REPO}" \
                --publish-depends ria-storage \
                {{ secrets.data.gh_derivs_repo | default('<organization>/<repo_name>') }}
        ```

        If successfull, the output in this case should be something like:

        ``` Text
        create_sibling_github(ok): [sibling repository 'github' created at https://github.com/<organization>/<repo_name>]
        configure-sibling(ok): . (sibling)
        action summary:
          configure-sibling (ok: 1)
          create_sibling_github (ok: 1)
        ```

        The repository should exist now in *GitHub*.

    === "When the GitHub repo has been manually created"

        ``` shell
        datalad siblings add --dataset . --name github \
                --pushurl git@github.com:{{ secrets.data.gh_derivs_repo | default('<organization>/<repo_name>') }}.git \
                --url https://github.com/{{ secrets.data.gh_derivs_repo | default('<organization>/<repo_name>') }}.git \
                --publish-depends ria-storage
        ```

- [ ] Push the configuration to the `github` sibling:
    ``` shell
    datalad push --to=github
    ```

    The output should be something like:

    ``` Text
    publish(ok): . (dataset) [refs/heads/master->github:refs/heads/master [new branch]]
    publish(ok): . (dataset) [refs/heads/git-annex->github:refs/heads/git-annex [new branch]]

    action summary:
       publish (ok: 2)
    ```

- [ ] Check that `master` is the default branch in the repository settings (in this case: [https://github.com/{{ secrets.data.gh_derivs_example_repo | default('<organization>/<repo_name>') }}/settings](https://github.com/{{ secrets.data.gh_derivs_example_repo | default('<organization>/<repo_name>') }}/settings))

## Nesting derivatives datasets

With the structure of derivatives we have defined above, we will then nest datalad datasets to obtain consistent global derivatives.
For example, let's nest the *FreeSurfer* derivatives into the `sourcedata/freesurfer` folder of the *fMRIPrep* derivatives of the piloting sessions with the reliability protocol.

- [ ] Change directory into the *superdataset* folder, ensure it's updated, and create a new branch (for caution)
    ``` shell
    export TOP_REPO=fmriprep-reliability-pilot
    export DERIVS_REPO=freesurfer-reliability-pilot

    cd hcph-${TOP_REPO}
    datalad update --how ff-only
    git checkout -b add/freesurfer-subdataset master
    ```

- [ ] Install the subdataset (in this case into `sourcedata/freesurfer`)
    ``` shell
    datalad install -d . \
                    -s https://github.com/{{ secrets.data.gh_derivs_repo | default('<organization>/<repo_name>') }}.git \
                    sourcedata/freesurfer
    ```

- [ ] Push the changes to the super-dataset:
    ``` shell
    datalad push --to=github
    ```

- [ ] Visit the *superdataset*'s *GitHub* repository:
    - [ ] Create a pull-request (PR)
    - [ ] Review the PR
    - [ ] Merge the PR

- [ ] Back to the host for data management, update the dataset:
    ``` shell
    cd hcph-${TOP_REPO}  # if necessary
    git checkout master
    datalad update --how ff-only
    ```

[1]: https://doi.org/10.5281/zenodo.808846 "Hanke, Michael, et al. “Datalad.” Open Source Software, 2021. doi:10.5281/zenodo.808846"
