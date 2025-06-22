import os
import pickle
import time
import arviz as az
import numpy as np

from joblib import Parallel, delayed

from simulate_sc import (
    simulate_sc_no_bias,
    simulate_sc_noisy_copies,
    simulate_sc_length_bias,
    simulate_sc_density_bias,
    simulate_sc_fns,
    simulate_sc_fps,
)
from bayesian_modeling import fit_mixture_model


def fit_edge(SC_matrices_flat, c, output_dir, time_file, mu_type="fixed"):
    start_time = time.time()
    print(f"Fitting edge {c} of {SC_matrices_flat.shape[1]}")
    pkl_file = os.path.join(output_dir, f"edge_{c:05d}.pkl")
    trace_file = os.path.join(output_dir, f"edge_{c:05d}_trace.nc")

    if os.path.exists(pkl_file):
        print(f"Loading existing results for edge {c}")
        with open(pkl_file, "rb") as f:
            return pickle.load(f)

    # Fit the Bayesian model to this edge repeated measures
    data_mean = np.mean(SC_matrices_flat[:, c])
    print("Sampling the trace for edge", c)
    trace, model, model_info = fit_mixture_model(
        SC_matrices_flat[:, c],
        mu_type=mu_type,
        mu_value=data_mean,
        draws=2000,
        n_tune=1000,
        progressbar=False,
        chains=4,
        cores=1,
    )
    var_names = ["pi0", "lambda_exp", "sigma"]
    param_values = {}
    if model_info["mu_type"] == "fixed":
        param_values["mu"] = data_mean
    else:
        var_names.append("mu")

    summary = az.summary(trace, var_names=var_names)
    for var in var_names:
        param_values[var] = summary.loc[var, "mean"]

    # Save parameter values to a pickle file
    with open(pkl_file, "wb") as f:
        pickle.dump(param_values, f)

    # Save full trace separately as NetCDF
    az.to_netcdf(trace, trace_file)

    # Save the time taken for fitting
    time_taken = time.time() - start_time

    with open(time_file, "a") as f:
        f.write(f"{c},{time_taken:.2f}\n")

    return param_values


## main
exp_start = time.time()
mu_type = "fixed"
output_dir = "/home/cprovins/projects/bayesian_sc/mixture_model_1"
atlas_path = "/data/probconnatlas/wm.connatlas.scale1.h5"
time_file = os.path.join(output_dir, "fitting_times.csv")
with open(time_file, "w") as f:
    f.write("edge,time_taken\n")

# Load simulated SC
SC_matrices, noise = simulate_sc_density_bias(
    atlas_path=atlas_path, connectome_atlas_as_ref=True, num_sessions=36
)
num_sessions = SC_matrices.shape[0]
atlas_dim = SC_matrices.shape[1]
# Keep only the upper triangle 
triu_indices = np.triu_indices(atlas_dim, k=0)
SC_matrices_triu = SC_matrices[:, triu_indices[0], triu_indices[1]]
SC_matrices_flat = SC_matrices_triu.reshape(num_sessions, -1)
SC_matrices_flat = np.nan_to_num(SC_matrices_flat, nan=0)

# Run in parallel
os.makedirs(output_dir, exist_ok=True)
n_jobs = 20  # or specify a number like 8
results = Parallel(n_jobs=n_jobs, backend="loky")(
    delayed(fit_edge)(SC_matrices_flat, c, output_dir, time_file, mu_type=mu_type)
    for c in range(SC_matrices_flat.shape[1])
)

# Write the total time taken to a CSV file
total_time = time.time() - exp_start
total_time_file = os.path.join(output_dir, "total_exp_time.csv")
with open(total_time_file, "w") as f:
    f.write("total_exp_time\n")
    f.write(f"{total_time:.2f}\n")
