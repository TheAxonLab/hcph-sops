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
