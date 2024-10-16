## Preparing a *DataLad*-enabled environment

### On CHUV's cluster

When HPC is planned for processing, *DataLad* will be required on that system(s).

- [ ] Start an interactive session on the HPC cluster

    ??? warning "Do not run the installation of *Conda* and *DataLad* in the login node"

        HPC systems typically recommend using their login nodes only for tasks related to job submission, data management, and preparing jobscripts.
        Therefore, the execution of resource-intensive tasks such as *fMRIPrep* or building containers on login nodes can negatively impact the overall performance and responsiveness of the system for all users.
        Interactive sessions are a great alternative when available and **should** be used when creating the *DataLad* dataset.
        For example, in the case of systems operating SLURM, the following command would open a new interactive session:
        ```
        srun --nodes=1 --ntasks-per-node=1 --time=01:00:00 --pty bash -i
        ```

- [ ] Install *DataLad*.
    Generally, the most convenient and user-sandboxed installation (i.e., without requiring elevated permissions) can be achieved by using *Conda*, but other alternatives (such as *lmod*) can be equally valid:

    === "Install *DataLad* with *Conda*"

        - [ ] Get and install *Conda* if it is not already deployed in the system:

            ``` shell
            wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
            bash Miniconda3-latest-Linux-x86_64.sh
            ```

        - [ ] Install *DataLad*:

            ``` shell
            conda install -c conda-forge -y "datalad>=1.0" datalad-container
            ```

    === "Install *DataLad* in HPC with *lmod* enabled"

        - [ ] Check the availability and dependencies for a specific Python version (here we check 3.8.2):

            ``` bash
            module spider Python/3.8.2
            ```

        - [ ] Load Python (please note `ml` below is a shorthand for `module load`)

            ``` bash
            ml GCCcore/9.3.0 Python/3.8.2
            ```

        - [ ] Update *pip*:

            ``` bash
            python -m pip --user -U pip
            ```

        - [ ] Install *DataLad*:

            ``` bash
            python -m pip install --user "datalad>=1.0" datalad-container
            ```

- [ ] Check datalad is properly installed, for instance:

    ``` shell
    $ datalad --version
    datalad 1.0.0
    ```

    ??? bug "*DataLad* crashes (*Conda* installations)"

        *DataLad* may fail with the following error:
        ``` py
        ImportError: cannot import name 'getargspec' from 'inspect' (/home/users/cprovins/miniconda3/lib/python3.11/inspect.py)
        ```

        In such a scenario, create a *Conda* environment with a lower version of Python, and re-install datalad
        ``` shell
        conda create -n "datalad" python=3.10
        conda activate datalad
        conda install -c conda-forge datalad datalad-container
        ```

- [ ] Configure your Git identity settings.

    ``` shell
    cd ~
    git config --global --add user.name "Jane Doe"
    git config --global --add user.email doe@example.com
    ```

### On UNIL's *Curnagl*

??? warning "Do not run the installation on the login node"

    HPC systems typically recommend using their login nodes only for tasks related to job submission, data management, and preparing jobscripts.
    Therefore, the execution of resource-intensive tasks such as *fMRIPrep* or building containers on login nodes can negatively impact the overall performance and responsiveness of the system for all users.
    Interactive sessions are a great alternative when available and **should** be used when creating the *DataLad* dataset.
    For example, in the case of systems operating SLURM, the following command would open a new interactive session:

    ```Bash
    salloc --partition=interactive --time=02:00:00 --cpus-per-task 12
    ```

- [ ] Install *Micromamba* following [*Curnagl*'s instructions](https://wiki.unil.ch/ci/books/high-performance-computing-hpc/page/using-mamba-to-install-conda-packages):
    - [ ] Add the following two lines to your `~/.bashrc` file:
        ```Bash
        export PATH="$PATH:/dcsrsoft/spack/external/micromamba"
        export MAMBA_ROOT_PREFIX="{{ secrets.data.curnagl_workdir | default('/work/FAC/SCHOOL/INSTITUTE/PI/PROJECT') }}/opt/mamba"
        ```

    - [ ] Instruct *Micromamba* to update your profile issuing the following command line:
        ```Bash
        micromamba shell init
        ```
    - [ ] Log out and back in

- [ ] Create a new environment called `datalad` with *Git annex* in it:
    ```Bash
    micromamba create -n datalad python=3.12 git-annex=*=alldep*
    ```
- [ ] Activate the environment
    ```Bash
    micromamba activate datalad
    ```
- [ ] Install *DataLad* and *DataLad-next*:
    ```Bash
    python -m pip install datalad datalad-next
    ```
- [ ] Configure your *Git* identity settings.

    ``` shell
    cd ~
    git config --global --add user.name "Jane Doe"
    git config --global --add user.email doe@example.com
    ```

## Installing the *DataLad* dataset

Wherever you want to process the data, you'll need to `datalad install` it before you can pull down (`datalad get`) the data.
To access the metadata (e.g., sidecar JSON files of the BIDS structure), you'll need to have access to the git repository that corresponds to the data (https://github.com/{{ secrets.data.gh_repo | default('&lt;organization&gt;/&lt;repo_name&gt;') }}.git)
To fetch the dataset from the RIA store, you will need your SSH key be added to the authorized keys at *Curnagl*.

??? important "Getting access to the RIA store"

    These steps must be done just once before you can access the dataset's data:

    - [ ] [Create a secure SSH key](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent) on the system(s) on which you want to install the dataset.
    - [ ] Send the SSH **public** key you just generated (e.g., `~/.ssh/id_ed25519.pub`) over email to Oscar at {{ secrets.email.oscar | default('*****@******') }}.


- [ ] Install and get the dataset normally:

    === "Installing the dataset without fetching data from annex"

        ``` shell
        datalad install https://github.com/{{ secrets.data.gh_repo | default('<organization>/<repo_name>') }}.git
        ```

    === "Installing the dataset and fetch all data from annex, with 8 parallel threads"

        ``` shell
        datalad install -g -J 8 https://github.com/{{ secrets.data.gh_repo | default('<organization>/<repo_name>') }}.git
        ```

!!! warning "Reconfiguring the RIA store on *Curnagl*"

    When on *Curnagl*, you'll need to *convert* the `ria-storage` remote
    on a local `ria-store` because you cannot ssh from *Curnagl* into itself:

    ```Bash
    git annex initremote --private --sameas=ria-storage curnagl-storage type=external externaltype=ora encryption=none url="ria+file://{{ secrets.data.curnagl_ria_store | default('<path>') }}"
    ```

In addition to reconfiguring the RIA store, we should execute `datalad get` within a compute node:

- [ ] Create a *sbatch* job prescription script called `datalad-get.sbatch`:
    ```Bash
    #!/bin/bash -l

    #SBATCH --account {{ secrets.data.curnagl_account | default('<PI>_<project_id>') }}

    #SBATCH --chdir {{ secrets.data.curnagl_workdir | default('<workdir>') }}/data/hcph-dataset
    #SBATCH --job-name datalad_get
    #SBATCH --partition cpu
    #SBATCH --cpus-per-task 12
    #SBATCH --mem 10G
    #SBATCH --time 05:00:00
    #SBATCH --export NONE

    #SBATCH --mail-type ALL
    #SBATCH --mail-user <your-email-address>
    #SBATCH --output /users/%u/logs/%x-%A-%a.out
    #SBATCH --error /users/%u/logs/%x-%A-%a.err


    micromamba run -n fmriprep datalad get -J${SLURM_CPUS_PER_TASK} .
    ```
- [ ] Submit the job:
    ```Bash
    sbatch datalad-get.sbatch
    ```

## Registering containers

We use *DataLad containers-run* to execute software while keeping track of provenance.
Prior to first use, containers must be added to *DataLad* as follows (example for *MRIQC*):

- [ ] Register the *MRIQC* container to the dataset

    === "Registering a *Singularity* container"

        ``` shell
        datalad containers-add \
            --call-fmt 'singularity exec --cleanenv -B {% raw %}{{${HOME}/tmp/}}:/tmp {img} {cmd}{% endraw %}' \
            mriqc \
            --url docker://nipreps/mriqc:{{ settings.versions.mriqc }}
        ```

        ??? important "Insert relevant arguments to the `singularity` command line with `--call-fmt`"

            In the example above, we configure the container's call to automatically *bind* (`-B` flag to mount the filesystem) the temporary folder.
            *MRIQC* will store the working directory there by default.
            Please replace the path with the appropriate path for your settings (i.e., laptop, cluster, etc.).

    === "Registering a *Docker* container"

        ``` shell
        datalad containers-add \
            --call-fmt 'docker run -u $( id -u ) -it -v {% raw %}{{${HOME}/tmp/}}:/tmp {img} {cmd}{% endraw %}' \
            mriqc \
            --url docker://nipreps/mriqc:{{ settings.versions.mriqc }}
        ```

    ??? info "Pinning a particular version of *MRIQC*"

        If a different version of *MRIQC* should be executed, replace the *Docker* image's tag (`{{ settings.versions.mriqc }}`) with the adequate version tag within the above command line.
