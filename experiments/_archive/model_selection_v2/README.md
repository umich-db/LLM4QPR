# Archived: `model_selection_v2` prototype (SUPERSEDED)

Archived **2026-05-28**. These files are the **old, single-objective Bayesian-optimization +
surrogate** model-selection prototype. They are **no longer the project's model-selection code**
and are kept here only for historical reference. Do not treat them as current.

## What's here
- `model_selection_v2.py` — the prototype search (surrogate/Bayesian-opt over a candidate pool).
- `visualize_search.py` — its 4-panel search visualizer (imports `model_selection_v2`).
- `ablation_feature_filter.py` — feature-filter ablation that `import`s `model_selection_v2`.
- `run_model_selection_v2.sh`, `run_model_selection.sh`, `demo_model_selection.sh` — its drivers/demo.
- `model_selection_v2_*.{json,log,png}` — output artifacts from prototype runs.

This cluster is self-contained: the three `.py` files only import each other and were imported by
nothing outside this directory, so archiving them breaks no live code.

## The CURRENT model-selection framework (use this instead)
Driven by **`experiments/analyze_overall.sh`** — a Pareto / round-based selection-under-compute-budget
approach (multi-objective: latency vs Q-error, hypervolume):

- `experiment_scripts/compare_round_pareto.py` — main driver.
  Flags seen in `analyze_overall.sh`: `--init_strategy {kmeans,stratified,random,stratified_arch_round,stratified_kmeans_round}`,
  `--rounds`, `--keep_ratio`, `--keep_strategy {stratified,topval}`, `--decision_epochs`.
- `experiment_scripts/select_pareto_next_round.py` — `pareto_levels()` (imported by the driver).
- `experiment_scripts/compare_selection_budgets.py`, `rank_correlation_epochs.py`, `ablate_init_and_keep.py`.
- `experiment_scripts/plot_hv_vs_hours.py` — HV-vs-compute-hours plot → `./model_selection.png`
  (`--settings C D F G H`, `--output`, `--title`).
- `experiment_scripts/plot_true_frontier.py` — true Pareto frontier → `./true_pareto_frontier.png`
  (`--annotate --logy --max_qerror --max_latency`).

## NOT archived (still live, despite the name)
- `experiment_scripts/random_model_selection.py` — the random-selection baseline, invoked by
  `master_random_inflatePRICE_e16_group_{A,B,C,D}.sh`. It only *mentions* `model_selection_v2` in a
  comment (shared candidate pool); it does not import it.
- `experiments/model_selection.png` — a **live output** of `plot_hv_vs_hours.py`, not a v2 artifact.
