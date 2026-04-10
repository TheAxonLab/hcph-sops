# Copyright 2025 The Axon Lab <theaxonlab@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# We support and encourage derived works from this project, please read
# about our expectations at
#
#     https://www.nipreps.org/community/licensing/
#
import pandas as pd
import pymc as pm
import numpy as np
import arviz as az
import matplotlib.pyplot as plt
import seaborn as sns
from IPython.display import display


def generate_synthetic_data(
    true_pi0, true_lambda, true_mu, true_sigma, n_samples, random_seed=None
):
    """
    Generate synthetic data from a mixture model.

    Parameters:
    -----------
    true_pi0 : float
        Proportion of unconnected regions (0 to 1)
    true_lambda : float
        Rate parameter for exponential distribution (unconnected regions)
    true_mu : float
        Mean density for connected regions
    true_sigma : float
        Standard deviation for connected regions
    n_samples : int
        Number of samples to generate
    random_seed : int, optional
        Random seed for reproducibility

    Returns:
    --------
    tuple
        (density_values, connection_status, parameter_dict)
    """
    if random_seed is not None:
        np.random.seed(random_seed)

    # Randomly assign connection status (0 = not connected, 1 = connected)
    connection_status = np.random.binomial(1, 1 - true_pi0, size=n_samples)

    # Generate density values based on connection status
    density_values = np.zeros(n_samples)

    # For unconnected regions (exponential distribution)
    unconnected_idx = connection_status == 0
    density_values[unconnected_idx] = np.random.exponential(
        scale=1 / true_lambda,  # Convert rate to scale
        size=np.sum(unconnected_idx),
    )

    # For connected regions (truncated normal distribution)
    connected_idx = connection_status == 1
    # Generate normal values and clip at 0
    normal_values = np.random.normal(
        loc=true_mu, scale=true_sigma, size=np.sum(connected_idx)
    )
    # Cast negative values to zero
    density_values[connected_idx] = np.clip(normal_values, 0, None)

    # Create parameter dictionary for reference
    params = {
        "pi0": true_pi0,
        "lambda_exp": true_lambda,
        "mu": true_mu,
        "sigma": true_sigma,
        "n_samples": n_samples,
    }

    return density_values, connection_status, params


def create_data_histogram(
    density_values,
    params,
    bins=50,
    title="Synthetic Density Data from Mixture Model",
    color="blue",
):
    """
    Create histogram of the synthetic data.

    Parameters:
    -----------
    density_values : array-like
        Synthetic density values
    params : dict
        Parameter dictionary
    bins : int, optional
        Number of histogram bins

    Returns:
    --------
    matplotlib.figure.Figure
        Figure with the histogram
    """
    fig = plt.figure(figsize=(10, 6))
    plt.hist(density_values, bins=bins, alpha=0.7, density=True, color=color)
    plt.axvline(
        x=params["mu"],
        color="red",
        linestyle="--",
        label=f"True mean for connected: {params['mu']}",
    )
    plt.title(title)
    plt.xlabel("Density")
    plt.ylabel("Frequency")
    plt.legend()
    return fig


def define_mixture_model(
    observed=None, mu_type="fixed", mu_value=0.8, mu_prior_mean=0.8, mu_prior_sigma=0.2
):
    with pm.Model() as model:
        # Prior for proportion of unconnected regions
        pi0 = pm.Beta("pi0", alpha=1.5, beta=2)

        # Prior for exponential rate parameter
        lambda_exp = pm.Gamma("lambda_exp", alpha=1, beta=10)

        # Prior for standard deviation of connected regions
        sigma = pm.HalfNormal("sigma", sigma=0.6)

        # Mean for connected regions - either fixed or learned
        if mu_type == "fixed":
            mu = mu_value  # Using fixed value
        else:  # "learned"
            mu = pm.Normal("mu", mu=mu_prior_mean, sigma=mu_prior_sigma)

        # Component 1: Exponential distribution for unconnected regions
        density_unconnected = pm.Exponential.dist(lam=lambda_exp)

        # Component 2: Truncated Normal for connected regions
        density_connected = pm.TruncatedNormal.dist(mu=mu, sigma=sigma, lower=0)

        # Mixture of the twos
        density = pm.Mixture(
            "density",
            w=[pi0, 1 - pi0],
            comp_dists=[density_unconnected, density_connected],
            observed=observed,
        )

        # Save the observed data for later use
        model_info = {
            "observed_data": observed,
            "mu_type": mu_type,
            "mu_value": mu_value if mu_type == "fixed" else None,
        }

    return model, model_info


def prior_preditive_sampling(
    params,
    mu_type="fixed",
    mu_value=0.8,
    mu_prior_mean=0.8,
    mu_prior_sigma=0.2,
    draws=100,
):
    model, model_info = define_mixture_model(
        mu_type=mu_type,
        mu_value=mu_value,
        mu_prior_mean=mu_prior_mean,
        mu_prior_sigma=mu_prior_sigma,
    )
    with model:
        prior_samples = pm.sample_prior_predictive(draws=draws)

    fig = create_data_histogram(
        prior_samples.prior["density"].values.flatten(),
        params,
        title="Prior samples",
        color="orange",
    )
    return fig


def fit_mixture_model(
    density_values,
    mu_type="fixed",
    mu_value=0.8,
    mu_prior_mean=0.8,
    mu_prior_sigma=0.2,
    draws=2000,
    n_tune=1000,
    random_seed=None,
    progressbar=True,
    chains=4,
    cores=4,
    repeat_fit=1,
):
    """
    Fit PyMC mixture model to the data.

    Parameters:
    -----------
    density_values : array-like
        Density values to fit
    mu_type : str, optional
        How to handle the mu parameter: "fixed" or "learned"
    mu_value : float, optional
        Value to use if mu_type is "fixed"
    mu_prior_mean : float, optional
        Prior mean for mu if mu_type is "learned"
    mu_prior_sigma : float, optional
        Prior standard deviation for mu if mu_type is "learned"
    draws : int, optional
        Number of posterior samples
    n_tune : int, optional
        Number of tuning steps
    random_seed : int, optional
        Random seed for reproducibility
    progressbar : bool, optional
        Whether to show a progress bar during sampling

    Returns:
    --------
    tuple
        (arviz.InferenceData, pm.Model, dict)
    """
    # Load the model from define_mixture_model
    model, model_info = define_mixture_model(
        observed=density_values,
        mu_type=mu_type,
        mu_value=mu_value,
        mu_prior_mean=mu_prior_mean,
        mu_prior_sigma=mu_prior_sigma,
    )
    with model:
        traces = []
        for i in range(repeat_fit):
            print(f"Fit {i} over {repeat_fit} in total...")
            # Sample from the posterior
            trace = pm.sample(
                draws,
                tune=n_tune,
                target_accept=0.9,
                return_inferencedata=True,
                random_seed=random_seed,
                progressbar=progressbar,
                chains=chains,
                cores=cores,
            )
            traces.append(trace)
        if len(traces) == 1:
            traces = traces[0]

    return traces, model, model_info


def create_analysis_plots(trace, params, model, model_info):
    """
    Create analysis plots without displaying them.

    Parameters:
    -----------
    trace : arviz.InferenceData
        Trace from the MCMC sampling
    params : dict
        True parameter values
    model_info : dict
        Information about the model and observed data

    Returns:
    --------
    dict
        Dictionary containing figures and summary statistics
    """
    results = {}

    # Get variables to summarize
    var_names = ["pi0", "sigma", "lambda_exp"]
    if model_info["mu_type"] == "learned":
        var_names.append("mu")

    # Summarize the results
    summary = az.summary(trace, var_names=var_names)
    results["summary"] = summary

    # Parameter comparison
    param_comparison = {}
    for param_name, pymc_name in [
        ("pi0", "pi0"),
        ("lambda_exp", "lambda_exp"),
        ("sigma", "sigma"),
        ("mu", "mu"),
    ]:
        # Skip mu if it was fixed in the model
        if param_name == "mu" and model_info["mu_type"] == "fixed":
            param_comparison[param_name] = {
                "true": params[param_name],
                "estimated": model_info["mu_value"],
                "note": "Fixed parameter (not estimated)",
            }
        elif pymc_name in summary.index:
            true_val = params[param_name]
            posterior_mean = summary.loc[pymc_name, "mean"]
            param_comparison[param_name] = {
                "true": true_val,
                "estimated": posterior_mean,
            }
    results["param_comparison"] = param_comparison

    # Trace plot
    fig_trace = plt.figure(figsize=(12, 8))
    trace_plot = az.plot_trace(trace, var_names=var_names)
    if params:
        parameter_list = [params["pi0"], params["sigma"], params["lambda_exp"]]
        if model_info["mu_type"] == "learned":
            parameter_list.append(params["mu"])
        for ax, true_value in zip(trace_plot[:, 0].ravel(), parameter_list):
            ax.axvline(
                true_value,
                color="red",
                linestyle="--",
                label=f"True value: {true_value}",
            )
        for ax, true_value in zip(trace_plot[:, 1].ravel(), parameter_list):
            ax.axhline(
                true_value,
                color="red",
                linestyle="--",
                label=f"True value: {true_value}",
            )
    plt.tight_layout()
    results["trace_plot"] = fig_trace

    # Energy plot
    fig_energy = plt.figure(figsize=(10, 6))
    az.plot_energy(trace)
    plt.tight_layout()
    results["energy_plot"] = fig_energy

    # Forest plot
    fig_forest = plt.figure(figsize=(10, 6))
    az.plot_forest(trace, var_names=var_names, combined=True, hdi_prob=0.95)
    plt.tight_layout()
    results["forest_plot"] = fig_forest

    # Autocorrelation plot
    fig_autocorr = plt.figure(figsize=(10, 10))
    az.plot_autocorr(trace, var_names=var_names)
    plt.tight_layout()
    results["autocorr_plot"] = fig_autocorr

    # Posterior predictive
    with model:
        # Sample from the posterior predictive
        posterior_predictive = pm.sample_posterior_predictive(trace)

    # Create the posterior predictive plot
    fig_pp = plt.figure(figsize=(10, 6))
    plt.hist(
        model_info["observed_data"],
        bins=50,
        alpha=0.7,
        density=True,
        color="blue",
        label="Observed Data",
    )

    sns.kdeplot(
        posterior_predictive.posterior_predictive["density"].values.flatten(),
        color="red",
        label="Posterior Predictive",
    )

    plt.title("Data vs. Posterior Predictive Distribution")
    plt.xlabel("Density")
    plt.ylabel("Density")
    plt.legend()
    plt.tight_layout()
    results["posterior_predictive_plot"] = fig_pp

    return results


def summary_across_fits(traces, params):
    """
    Create summary statistics across multiple fits.

    Parameters:
    -----------
    traces : list
        List of arviz.InferenceData objects
    params : dict
        True parameter values

    Returns:
    --------
    dict
        Dictionary with summary statistics
    """
    print("\nSummary statistics across multiple fits:")
    summaries = []
    for trace in traces:
        summary = az.summary(trace)

        summary["true_value"] = summary.index.map(
            lambda param: params.get(param, np.nan)
        )
        summary["estimation_error"] = abs(summary["mean"] - summary["true_value"])
        summary["relative_error%"] = (
            summary["estimation_error"] / summary["true_value"] * 100
        )
        summary["in_94%_hdi"] = summary.apply(
            lambda row: row["hdi_3%"] <= row["true_value"] <= row["hdi_97%"], axis=1
        )
        summaries.append(summary)

    # Combine all runs into a single DataFrame
    all_summaries = []
    for i, summary in enumerate(summaries):
        summary = summary.copy()
        summary["run"] = i
        summary["param"] = summary.index
        all_summaries.append(summary)

    all_summaries = pd.concat(all_summaries, ignore_index=True)

    rmse_per_param = (
        all_summaries.groupby("param")
        .apply(lambda g: np.sqrt(np.mean(g["estimation_error"] ** 2)))
        .rename("rmse")
    )
    coverage_per_param = (
        all_summaries.groupby("param")["in_94%_hdi"].mean().rename("coverage%")
    )

    summary_stats = pd.concat([rmse_per_param, coverage_per_param], axis=1)
    display(summary_stats)

    return summary_stats, all_summaries


def run_simulation(
    true_pi0=0.3,
    true_lambda=2.0,
    true_mu=0.8,
    true_sigma=0.15,
    n_samples=36,
    draws=2000,
    mu_type="fixed",
    mu_prior_mean=0.8,
    mu_prior_sigma=0.2,
    random_seed=None,
    display_plots=False,
    progressbar=True,
    repeat_fit=1,
):
    """
    Run a complete simulation and return results.

    Parameters:
    -----------
    true_pi0 : float
        Proportion of unconnected regions (0 to 1)
    true_lambda : float
        Rate parameter for exponential distribution (unconnected regions)
    true_mu : float
        Mean density for connected regions
    true_sigma : float
        Standard deviation for connected regions
    n_samples : int
        Number of repeated measures
    draws : int
        Number of trace samples to generate
    mu_type : str
        How to handle the mu parameter: "fixed" or "learned"
    mu_prior_mean : float
        Prior mean for mu if mu_type is "learned"
    mu_prior_sigma : float
        Prior standard deviation for mu if mu_type is "learned"
    random_seed : int
        Random seed for reproducibility
    display_plots : bool
        Whether to display plots immediately (otherwise they're just returned)

    Returns:
    --------
    dict
        Dictionary with all plots and results
    """
    results = {}

    print(f"Simulation with parameters:")
    print(f"- pi0 (proportion unconnected): {true_pi0}")
    print(f"- lambda (exponential rate): {true_lambda}")
    print(f"- mu (connected mean): {true_mu}")
    print(f"- sigma (connected std): {true_sigma}")
    print(f"- draws: {draws}")
    print(f"- n_samples: {n_samples}")
    print(f"- mu_type: {mu_type}")
    print(f"- repeat_fit: {repeat_fit}")
    if mu_type == "learned":
        print(f"- mu_prior_mean: {mu_prior_mean}")
        print(f"- mu_prior_sigma: {mu_prior_sigma}")
    print("-" * 50)

    # Generate data
    print("Generating synthetic data...")
    density_values, connection_status, params = generate_synthetic_data(
        true_pi0, true_lambda, true_mu, true_sigma, n_samples, random_seed
    )
    results["data"] = {
        "density_values": density_values,
        "connection_status": connection_status,
        "params": params,
        "repeat_fit": repeat_fit,
    }

    # Create data histogram
    print("Creating data histogram...")
    data_fig = create_data_histogram(density_values, params)
    results["data_histogram"] = data_fig

    # Prior predictive sampling
    print("Drawing prior predictive samples...")
    mu_value = true_mu if mu_type == "fixed" else None
    prior_fig = prior_preditive_sampling(
        params,
        mu_type=mu_type,
        mu_value=mu_value,
        mu_prior_mean=mu_prior_mean,
        mu_prior_sigma=mu_prior_sigma,
        draws=1000,
    )
    results["prior_sampling_histogram"] = prior_fig

    # Fit model
    print("Fitting PyMC model (this may take a few minutes)...")
    trace, model, model_info = fit_mixture_model(
        density_values,
        mu_type=mu_type,
        mu_value=mu_value,
        mu_prior_mean=mu_prior_mean,
        mu_prior_sigma=mu_prior_sigma,
        draws=draws,
        n_tune=1000,
        random_seed=random_seed,
        progressbar=progressbar,
        repeat_fit=repeat_fit,
    )
    results["model_info"] = model_info
    results["trace"] = trace

    # Create analysis plots
    print("Creating analysis plots...")
    summary_stats = None
    all_summaries = None
    if isinstance(trace, list) and len(trace) > 1:
        summary_stats, all_summaries = summary_across_fits(trace, params)
        results["summary_stats"] = summary_stats
        results["all_summaries"] = all_summaries
        print("Warning: the analysis plots are computed only on the first trace...")
        trace = trace[0]

    analysis_results = create_analysis_plots(trace, params, model, model_info)
    results.update(analysis_results)

    if display_plots:
        display_simulation_results(results)

    return results


def display_simulation_results(results):
    """
    Display all plots and results from a previously run simulation.

    Parameters:
    -----------
    results : dict
        Dictionary with simulation results
    """
    print("Simulation results:")
    print("-" * 50)

    print("\nParameter values:")
    params = results["data"]["params"]
    for param, value in params.items():
        print(f"- {param}: {value}")

    print("\nParameter comparison:")
    for param, values in results["param_comparison"].items():
        if "note" in values:
            print(
                f"{param}: True = {values['true']:.3f}, Value = {values['estimated']:.3f} ({values['note']})"
            )
        else:
            print(
                f"{param}: True = {values['true']:.3f}, Estimated = {values['estimated']:.3f}"
            )

    print("\nSummary statistics:")
    summary = results["summary"]
    print(f"Model parameters {params}")
    # Add parameter estimation error to the summary
    summary["true_value"] = summary.index.map(lambda param: params.get(param, np.nan))
    summary["estimation_error"] = summary.index.map(
        lambda param: abs(summary.loc[param, "mean"] - params.get(param, np.nan))
    )
    summary["relative_error%"] = (
        summary["estimation_error"] / summary["true_value"] * 100
    )
    display(summary)

    print("\nParameter comparison:")
    for param, values in results["param_comparison"].items():
        if "note" in values:
            print(
                f"{param}: True = {values['true']:.3f}, Value = {values['estimated']:.3f} ({values['note']})"
            )
        else:
            print(
                f"{param}: True = {values['true']:.3f}, Estimated = {values['estimated']:.3f}"
            )

    print("\nData histogram:")
    display(results["data_histogram"])

    print("\nPrior predictive histogram:")
    display(results["prior_sampling_histogram"])

    print("\nTrace plot:")
    display(results["trace_plot"])

    print("\nEnergy plot:")
    display(results["energy_plot"])

    print("\nForest plot:")
    display(results["forest_plot"])

    print("\nAutocorrelation plot:")
    display(results["autocorr_plot"])

    if "posterior_predictive_plot" in results:
        print("\nPosterior predictive check:")
        display(results["posterior_predictive_plot"])
