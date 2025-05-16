import pickle
import os

from bayesian_modeling import run_simulation

output_dir = "/home/cprovins/projects/bayesian_sc/mixture_model_1"

pi0_values = [0.05, 0.1, 0.2, 0.4, 0.6, 0.8, 0.9, 0.95]
results_multi_pi0 = {}
for pi0 in pi0_values:
    print(f"Running simulation with pi0 = {pi0}")
    results_multi_pi0[pi0] = run_simulation(
        true_pi0=pi0,
        true_lambda=2.0,
        true_mu=3.0,
        true_sigma=0.5,
        display_plots=False,
        progressbar=False,
        random_seed=None,
        repeat_fit=30,
    )
with open(os.path.join(output_dir, "results_multi_pi0.pkl"), "wb") as f:
    pickle.dump(results_multi_pi0, f)

mu_values = [1.0, 2.0, 3.0, 5.0, 8.0, 20.0, 30.0, 1000, 10000]
results_multi_mu = {}
for mu in mu_values:
    print(f"Running simulation with mu = {mu}")
    results_multi_mu[mu] = run_simulation(
        true_pi0=0.1,
        true_lambda=2.0,
        true_mu=mu,
        true_sigma=0.5,
        display_plots=False,
        progressbar=False,
        random_seed=None,
        repeat_fit=30,
    )

with open(os.path.join(output_dir, "results_multi_mu_.pkl"), "wb") as f:
    pickle.dump(results_multi_mu, f)

mu_values = [0.1, 0.2, 0.5, 0.7]
results_multi_mu = {}
for mu in mu_values:
    print(f"Running simulation with mu = {mu}")
    results_multi_mu[mu] = run_simulation(
        true_pi0=0.1,
        true_lambda=2.0,
        true_mu=mu,
        true_sigma=0.5,
        display_plots=False,
        progressbar=False,
        random_seed=None,
        repeat_fit=20,
    )

with open(os.path.join(output_dir, "results_multi_mu_2.pkl"), "wb") as f:
    pickle.dump(results_multi_mu, f)
