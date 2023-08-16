import fnmatch


def heur(physinfo, take=""):
    """
    Set of if .. elif statements to fill BIDS names.

    It requires the user (you!) to adjust it accordingly!
    It needs an ``if`` or ``elif`` statement for each file that
    needs to be processed.
    The statement will test if the ``physinfo``:
        - is similar to a string (first case), or
        - exactly matches a string (second case).

    Parameters
    ----------
    physinfo: str
        Name of an input file that should be bidsified (See Notes)

    Returns
    -------
    info: dictionary of str
        Dictionary containing BIDS keys

    Notes
    -----
    The `if ..` structure should always be similar to
    ```
    if physinfo == 'somepattern':
        info['var'] = 'somethingelse'
    ```
    or, in case it's a partial match
    ```
    if fnmatch.fnmatchcase(physinfo, '*somepattern?'):
        info['var'] = 'somethingelse'
    ```
    Where:
        - `physinfo` and `info` are dedicated keywords,
        - 'somepattern' is the name of the file,
        - 'var' is a bids key in the list below
        - 'somethingelse' is the value of the key
    """
    info = {}
    # ################################# #
    # ##        Modify here!         ## #
    # ##                             ## #
    # ##  Possible variables are:    ## #
    # ##    -info['task'] (required) ## #
    # ##    -info['run']             ## #
    # ##    -info['rec']             ## #
    # ##    -info['acq']             ## #
    # ##    -info['dir']             ## #
    # ##                             ## #
    # ##  Remember that they are     ## #
    # ##  dictionary keys            ## #
    # ##  See example below          ## #
    # ################################# #

    if fnmatch.fnmatchcase(physinfo, "*multiscan*"):
        if take == "01":
            info["task"] = "qct"
        if take == "02":
            info["task"] = "rest"
        if take == "03":
            info["task"] = "bht"
    elif fnmatch.fnmatchcase(physinfo, "*.acq*"):
        if take == "01":
            info["task"] = "qct"
        if take == "02":
            info["task"] = "rest"
        if take == "03":
            info["task"] = "bht"

    # ############################## #
    # ## Don't modify below this! ## #
    # ############################## #
    return info
