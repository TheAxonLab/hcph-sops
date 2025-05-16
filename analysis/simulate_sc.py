import numpy as np
import h5py


def get_ref_sc(
    connectome_atlas=True,
    atlas_path="/data/probconnatlas/wm.connatlas.scale3.h5",
    atlas_dim=64,
    scale=0.01,
    shape=0.5,
):
    """
    Determine which SC matrix to use as reference, the density matrix from the connectome atlas or a matrix randomly generated from a lognormal distribution.

    Parameters:
    -----------
    connectome_atlas : bool, optional
        If True, the SC matrix is loaded from the connectome atlas specified by `atlas_path`.
        If False, the SC matrix is simulated using a log-normal distribution. Default is True.
    atlas_path : str, optional
        Path to the connectome atlas file in HDF5 format. This file should contain the SC matrix
        under the key `matrices/numbStlines`. Default is "/data/wm.connatlas.scale3.h5".
    atlas_dim : int, optional
        The dimension of the SC matrix to simulate if `connectome_atlas` is False. The resulting
        matrix will have shape `(atlas_dim, atlas_dim)`. Default is 64.
    scale : float, optional
        The scale parameter for the log-normal distribution used to simulate the SC matrix.
        This parameter determines the mean of the distribution. Default is 0.01.
    shape : float, optional
        The shape parameter (sigma) for the log-normal distribution used to simulate the SC matrix.
        This parameter determines the spread of the distribution. Default is 0.5.
    Returns:
    --------
    np.ndarray
        A 2D numpy array representing the reference SC matrix.
    """
    if connectome_atlas:
        print("Using the connectome atlas as reference SC matrix.")
        with h5py.File(atlas_path, "r") as f:
            SC_matrix = np.array(f["matrices"]["numbStlines"])
            # Because at scale 3, all regions are of similar size, the density and average number of streamlines are approximately proportional
    else:
        print("Simulating a reference SC matrix using a log-normal distribution.")
        ## Fix the random seed the same way as in the defacing registered report (RR)
        day = 231108  # day and time the journal published our HCPh stage 1 RR
        time = 105017
        random_seed = day + time
        rng = np.random.default_rng(random_seed)

        ## Simulate a reference structural connectivity (SC) matrix

        # SC matrices typically follow a heavy-tailed distribution, with a few strong connections and many weak ones.
        # We thus use a log-normal distribution to simulate SC value.
        SC_matrix = rng.lognormal(
            mean=np.log(scale), sigma=shape, size=(atlas_dim, atlas_dim)
        )

        # Make it symmetric
        SC_matrix = (SC_matrix + SC_matrix.T) / 2

        # Set diagonal to 0 (no self-connections)
        np.fill_diagonal(SC_matrix, 0)

        assert SC_matrix.shape == (atlas_dim, atlas_dim)

    return SC_matrix


def simulate_sc_density_bias(
    num_sessions=36,
    connectome_atlas_as_ref=True,
    atlas_path="/data/probconnatlas/wm.connatlas.scale3.h5",
    atlas_dim=64,
    bias_density=40,
    small_noise_scale=0.2,
    high_noise_scale=0.5,
):
    """
    Simulate structural connectivity (SC) matrices with density-based noise bias.

     This function generates a reference SC matrix using a predefined atlas and
     creates multiple noisy copies to simulate between-session variability.
     Weaker connections (below a specified density percentile) are subjected to
     higher noise to simulate greater variability in these connections.

     Parameters
     ----------
     num_sessions : int, optional
         Default is 36.
     connectome_atlas_as_ref : bool, optional
         Whether to use a predefined connectome atlas as the reference SC matrix.
         Default is True.
     bias_density : float, optional
         The percentile threshold (0-100) used to identify weaker connections
         in the reference SC matrix. Connections below this threshold are subjected
         to higher noise. Default is 20.
     small_noise_scale : float, optional
         The standard deviation of the normal distribution used to generate
         small noise added to all connections. Default is 0.0005.
     high_noise_scale : float, optional
         The standard deviation of the normal distribution used to generate
         higher noise added to weaker connections. Default is 0.002.

     Returns
     -------
         The simulated SC matrices stored in a 3D numpy array of shape (num_sessions, atlas_dim, atlas_dim), where `atlas_dim` is the dimensionality of the
         brain atlas (number of regions).
    """
    SC_matrix = get_ref_sc(
        connectome_atlas=connectome_atlas_as_ref,
        atlas_path=atlas_path,
        atlas_dim=atlas_dim,
    )
    atlas_dim = SC_matrix.shape[1]

    ## Copy this matrix multiple time to simulate multiple sessions of the same subject
    ## Add noise in the copies to simulate between-session variability
    SC_matrices = np.zeros((num_sessions, atlas_dim, atlas_dim))

    # Identify the 20th percentile threshold for the connection values in the reference SC matrix (without considering unexisting connections)
    percentile_threshold = np.percentile(SC_matrix[SC_matrix > 0], bias_density)

    # Add noise to each duplicate
    noise_list = []
    for i in range(num_sessions):
        noise = np.random.normal(loc=0, scale=small_noise_scale, size=SC_matrix.shape)
        higher_noise = np.random.normal(
            loc=0, scale=high_noise_scale, size=SC_matrix.shape
        )

        # Apply higher noise to connections below the 20th percentile to simulate higher variability in weaker connections
        noise[SC_matrix <= percentile_threshold] += higher_noise[
            SC_matrix <= percentile_threshold
        ]
        noise_list.append(noise)

        # Replace NaN with 0, so non-existing connections are also affected by the noise
        SC_matrix = np.nan_to_num(SC_matrix, nan=0)
        SC_matrices[i, :, :] = SC_matrix + noise

        # SC cannot have negative values so if the value gets negative cast it to 0
        SC_matrices[i, :, :] = np.maximum(SC_matrices[i, :, :], 0)

    print(
        f"Simulated a series of {SC_matrices.shape[0]} SC matrices of shape ({SC_matrices.shape[1]}x{SC_matrices.shape[2]}) with higher variability (std={high_noise_scale}) in lower density connections."
    )
    # Test whether the shape is as expected
    assert SC_matrices.shape == (num_sessions, atlas_dim, atlas_dim)

    return SC_matrices, np.array(noise_list)


def simulate_sc_length_bias(
    num_sessions=36,
    connectome_atlas_as_ref=True,
    atlas_path="/data/probconnatlas/wm.connatlas.scale3.h5",
    bias_length=20,
    small_noise_scale=0.0001,
    high_noise_scale=0.5,
):
    """
    Simulates structural connectivity (SC) matrices with a length bias, introducing
    higher variability in longer connections.

    Parameters:
    -----------
    num_sessions : int, optional
        Number of SC matrices to simulate. Default is 36.
    connectome_atlas_as_ref : bool, optional
        If True, uses the connectome atlas as the reference SC matrix, otherwise randomly generate a reference SC matrix based on a lognormal distribution. Default is True.
    atlas_path : str, optional
        Path to the connectome atlas file in HDF5 format. Default is "/data/wm.connatlas.scale3.h5".
    bias_length : int, optional
        Percentile threshold for determining long connections. Connections longer than
        this percentile will have higher noise applied. Default is 20.
    small_noise_scale : float, optional
        Standard deviation of the small gaussian noise added to all connections. Default is 0.0005.
    high_noise_scale : float, optional
        Standard deviation of the higher gaussian noise added to long connections. Default is 0.002.
    Returns:
    --------
    np.ndarray
        The simulated SC matrices stored in a 3D numpy array of shape (num_sessions, atlas_dim, atlas_dim), where `atlas_dim` is the dimensionality of the
        brain atlas (number of regions).
    Notes:
    ------
    - We are using the length matrix of the connectome atlas of Alemán-Gómez et al. (2022)
        to determine the streamline length distribution. Please download the atlas from
        https://doi.org/10.5281/zenodo.4919132.
    """
    SC_matrix = get_ref_sc(
        connectome_atlas=connectome_atlas_as_ref, atlas_path=atlas_path, atlas_dim=243
    )  # If we simulate the SC matrix, we need to set the atlas_dim to 243 to match the shape of the length matrix.

    with h5py.File(atlas_path, "r") as f:
        length_matrix = np.array(f["matrices"]["length"])

    atlas_dim = SC_matrix.shape[1]
    SC_matrices = np.zeros((num_sessions, atlas_dim, atlas_dim))

    # Identify the 20th percentile of longest connection
    percentile_threshold = np.percentile(length_matrix[length_matrix > 0], bias_length)
    long_connections = length_matrix > percentile_threshold

    # Add noise to each duplicate
    noise_list = []
    for i in range(num_sessions):
        noise = np.random.normal(loc=0, scale=small_noise_scale, size=SC_matrix.shape)
        higher_noise = np.random.normal(
            loc=0, scale=high_noise_scale, size=SC_matrix.shape
        )

        # Apply higher noise to long connections
        noise[long_connections] += higher_noise[long_connections]

        noise_list.append(noise)

        SC_matrices[i, :, :] = SC_matrix + noise

        # SC cannot have negative values so if the value gets negative cast it to 0
        SC_matrices[i, :, :] = np.maximum(SC_matrices[i, :, :], 0)

    print(
        f"Simulated a series of {SC_matrices.shape[0]} SC matrices of shape ({SC_matrices.shape[1]}x{SC_matrices.shape[2]}) with higher variability (std={high_noise_scale}) in long connections."
    )

    return SC_matrices, np.array(noise_list)


def simulate_sc_noisy_copies(
    num_sessions=36,
    connectome_atlas_as_ref=True,
    atlas_path="/data/probconnatlas/wm.connatlas.scale3.h5",
    noise_scale=0.0001,
):
    """
    Simulates structural connectivity (SC) matrices with a length bias, introducing
    higher variability in longer connections.

    Parameters:
    -----------
    num_sessions : int, optional
        Number of SC matrices to simulate. Default is 36.
    connectome_atlas_as_ref : bool, optional
        If True, uses the connectome atlas as the reference SC matrix, otherwise randomly generate a reference SC matrix based on a lognormal distribution. Default is True.
    atlas_path : str, optional
        Path to the connectome atlas file in HDF5 format. Default is "/data/wm.connatlas.scale3.h5".
    noise_scale : float, optional
        Standard deviation of the gaussian noise added to all connections. Default is 0.0001.
    Returns:
    --------
    np.ndarray
        The simulated SC matrices stored in a 3D numpy array of shape (num_sessions, atlas_dim, atlas_dim), where `atlas_dim` is the dimensionality of the
        brain atlas (number of regions).
    """
    SC_matrix = get_ref_sc(
        connectome_atlas=connectome_atlas_as_ref, atlas_path=atlas_path, atlas_dim=243
    )  # If we simulate the SC matrix, we need to set the atlas_dim to 243 to match the shape of the length matrix.

    atlas_dim = SC_matrix.shape[1]
    SC_matrices = np.zeros((num_sessions, atlas_dim, atlas_dim))
    # Add noise to each duplicate
    noise_list = []
    for i in range(num_sessions):
        noise = np.random.normal(loc=0.0, scale=noise_scale, size=SC_matrix.shape)
        noise_list.append(noise)

        SC_matrices[i, :, :] = SC_matrix + noise

        # SC cannot have negative values so if the value gets negative cast it to 0
        SC_matrices[i, :, :] = np.maximum(SC_matrices[i, :, :], 0)

    print(
        f"Simulated a series of {SC_matrices.shape[0]} SC matrices of shape ({SC_matrices.shape[1]}x{SC_matrices.shape[2]}) with noisy copies (std={noise_scale})."
    )

    return SC_matrices, np.array(noise_list)


def simulate_sc_no_bias(
    num_sessions=36,
    connectome_atlas_as_ref=True,
    atlas_path="/data/probconnatlas/wm.connatlas.scale3.h5",
):
    """
    Simulates structural connectivity (SC) matrices with a length bias, introducing
    higher variability in longer connections.

    Parameters:
    -----------
    num_sessions : int, optional
        Number of SC matrices to simulate. Default is 36.
    connectome_atlas_as_ref : bool, optional
        If True, uses the connectome atlas as the reference SC matrix, otherwise randomly generate a reference SC matrix based on a lognormal distribution. Default is True.
    atlas_path : str, optional
        Path to the connectome atlas file in HDF5 format. Default is "/data/wm.connatlas.scale3.h5".
    Returns:
    --------
    np.ndarray
        The simulated SC matrices stored in a 3D numpy array of shape (num_sessions, atlas_dim, atlas_dim), where `atlas_dim` is the dimensionality of the
        brain atlas (number of regions).
    """
    SC_matrix = get_ref_sc(
        connectome_atlas=connectome_atlas_as_ref, atlas_path=atlas_path, atlas_dim=243
    )  # If we simulate the SC matrix, we need to set the atlas_dim to 243 to match the shape of the length matrix.
    atlas_dim = SC_matrix.shape[1]
    SC_matrices = np.zeros((num_sessions, atlas_dim, atlas_dim))
    for i in range(num_sessions):
        SC_matrices[i, :, :] = SC_matrix
        # SC cannot have negative values so if the value gets negative cast it to 0
        SC_matrices[i, :, :] = np.maximum(SC_matrices[i, :, :], 0)

    print(
        f"Simulated a series of {SC_matrices.shape[0]} identical SC matrices of shape ({SC_matrices.shape[1]}x{SC_matrices.shape[2]})."
    )

    return SC_matrices


def simulate_sc_fps(
    num_sessions=36,
    atlas_path="/data/probconnatlas/wm.connatlas.scale3.h5",
    fps_perc=20,
    impute_perc=20,
):
    """
    Simulates repeated structural connectivity (SC) matrices with false positives.

    Parameters:
    -----------
    num_sessions : int, optional
        The number of SC matrices (sessions) to simulate. Default is 36.
    fps_perc : float, optional
        The percentage of false positives to introduce. Default is 20.
    impute_perc : float, optional
        The percentile of the density distribution used to set the density of the false positives. Default is 20.
    Returns:
    --------
    np.ndarray
        The simulated SC matrices stored in a 3D numpy array of shape (num_sessions, atlas_dim, atlas_dim), where `atlas_dim` is the dimensionality of the
        brain atlas (number of regions).
    Notes:
    ------
    - This function works only with the connectome atlas from Alemán-Gómez et al. (2022) as reference, because we assume that no connection is encoded as NaN.
      Please download the atlas from https://doi.org/10.5281/zenodo.4919132.
    """
    SC_matrix = get_ref_sc(
        atlas_path=atlas_path, connectome_atlas=True
    )  # This function works only with the connectome atlas as reference, because we assume that no connection is encoded as NaN.
    atlas_dim = SC_matrix.shape[1]

    # Copy the reference matrix unaltered for each sessions, we will introduce changes below
    SC_matrices = np.repeat(SC_matrix[np.newaxis, :, :], num_sessions, axis=0)
    assert SC_matrices.shape == (num_sessions, atlas_dim, atlas_dim)

    # Identify the connections that do not exist
    nan_indices = np.argwhere(np.isnan(SC_matrix))
    num_to_select = int(len(nan_indices) * (fps_perc / 100))

    # Identify the 20th percentile of the density distribution
    density_percentile = np.percentile(SC_matrix[~np.isnan(SC_matrix)], impute_perc)
    print(
        f"SC simulation: at each session impute the {impute_perc}th density percentile ({density_percentile:.3f}) into random {fps_perc}% of NaN values ({num_to_select})."
    )

    for i in range(num_sessions):
        # Randomly select 20% of the connections that do not exist (encoded as NaN)
        selected_indices = nan_indices[
            np.random.choice(len(nan_indices), num_to_select, replace=False)
        ]

        # Verify that SC_matrix is NaN in all selected_indices
        for idx in selected_indices:
            assert np.isnan(SC_matrix[idx[0], idx[1]]), f"SC_matrix at {idx} is not NaN"

        # Impute the 20th percentile of the density distribution into the selected indices
        for idx in selected_indices:
            SC_matrices[i, idx[0], idx[1]] = density_percentile

        # Verify that the expected number of false positives has been introduced
        assert (
            len(np.argwhere(np.isnan(SC_matrices[i])))
            == len(nan_indices) - num_to_select
        ), f"Session {i}: Number of NaN values is not as expected"

    return SC_matrices


def simulate_sc_fns(
    num_sessions=36,
    atlas_path="/data/probconnatlas/wm.connatlas.scale3.h5",
    consistency_perc=20,
    fns_perc=20,
):
    """
    Simulates repeated structural connectivity (SC) matrices with false negatives.

    Parameters:
    -----------
    num_sessions : int, optional
        The number of SC matrices (sessions) to simulate. Default is 36.
    consistency_perc : float, optional
        The percentage of connections to select for low consistency. Default is 20.
    fns_perc : float, optional
        The percentage of false negatives to introduce among the connections selected for low consistency. Default is 20.
    Returns:
    --------
    np.ndarray
        The simulated SC matrices stored in a 3D numpy array of shape (num_sessions, atlas_dim, atlas_dim), where `atlas_dim` is the dimensionality of the
        brain atlas (number of regions).
    Notes:
    ------
    - This function uses the consistency matrix from the connectome atlas Alemán-Gómez et al. (2022) to target not consistent connections to remove.
      Please download the atlas from https://doi.org/10.5281/zenodo.4919132.
    """
    SC_matrix = get_ref_sc(
        atlas_path=atlas_path, atlas_dim=243
    )  # If we simulate the SC matrix, we need to set the atlas_dim to 243 to match the shape of the consistency matrix.
    atlas_dim = SC_matrix.shape[1]

    with h5py.File(atlas_path, "r") as f:
        consistency_matrix = np.array(f["matrices"]["consistency"])

    # Copy the reference matrix unaltered for each sessions, we will introduce changes below
    SC_matrices = np.repeat(SC_matrix[np.newaxis, :, :], num_sessions, axis=0)
    assert SC_matrices.shape == (num_sessions, atlas_dim, atlas_dim)

    # Identify the connections with the lowest consistency
    consistency_threshold = np.percentile(
        consistency_matrix[consistency_matrix > 0], consistency_perc
    )
    low_consistency_indices = np.argwhere(
        (consistency_matrix < consistency_threshold) & (consistency_matrix > 0)
    )  # Do not touch non-existing connections (consistency = 0)
    num_to_select = int(len(low_consistency_indices) * (fns_perc / 100))

    print(
        f"SC simulation: at each session randomly remove {fns_perc}% of the connections with a consistency in the lowest {consistency_perc}th percentile ({num_to_select})."
    )

    for i in range(num_sessions):
        # Randomly select 20% of the low consistency connections
        selected_indices = low_consistency_indices[
            np.random.choice(len(low_consistency_indices), num_to_select, replace=False)
        ]

        # Remove the selected connections by setting them to NaN
        for idx in selected_indices:
            SC_matrices[i, idx[0], idx[1]] = np.nan

        # Verify that the expected number of false negatives has been introduced
        assert (
            len(np.argwhere(np.isnan(SC_matrices[i])))
            == len(np.argwhere(np.isnan(SC_matrix))) + num_to_select
        ), f"Session {i}: Number of NaN values is not as expected"

    return SC_matrices
