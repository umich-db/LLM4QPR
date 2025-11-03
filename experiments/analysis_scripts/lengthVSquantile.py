import os
import argparse

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

from sklearn.linear_model import HuberRegressor
from sklearn.metrics import r2_score

def format_k(x, pos):
    if x >= 1000:
        return f"{int(x/1000)}k"
    return str(int(x))

def compute_bucket_percentiles(
    plan_lengths: np.ndarray,
    errors:       np.ndarray,
    num_buckets:  int
):
    """
    Splits the data into `num_buckets` equal‐width bins based on plan_lengths,
    then for each bin computes:
        - bucket_center (midpoint of that bin’s edges)
        - median_error = 50th percentile of errors within that bin
        - p90_error   = 90th percentile of errors within that bin
    Returns three arrays, each of shape (M,), where M <= num_buckets is the
    number of non‐empty bins:
        bucket_centers, median_errors, p90_errors
    """

    x_flat = plan_lengths.flatten()  # shape (n,)
    y_flat = errors                  # shape (n,)

    # 1) Compute equal‐width edges over [min(x), max(x)]
    x_min, x_max = float(x_flat.min()), float(x_flat.max())
    edges = np.linspace(x_min, x_max, num_buckets + 1)

    bucket_centers = []
    medians = []
    p90s = []
    p95s = []

    # 2) For each bucket, collect points and compute percentiles if nonempty
    for i in range(num_buckets):
        left_edge = edges[i]
        right_edge = edges[i + 1] if i < (num_buckets - 1) else edges[i + 1] + 1e-9

        mask = (x_flat >= left_edge) & (x_flat < right_edge)
        if not np.any(mask):
            # skip empty buckets
            continue

        y_bucket = y_flat[mask]
        center = 0.5 * (left_edge + right_edge)
        median_val = np.percentile(y_bucket, 50)
        p90_val   = np.percentile(y_bucket, 90)
        p95_val   = np.percentile(y_bucket, 95)

        bucket_centers.append(center)
        medians.append(median_val)
        p90s.append(p90_val)
        p95s.append(p95_val)

    return (
        np.array(bucket_centers).reshape(-1, 1),  # shape (M,1), for sklearn
        np.array(medians),
        np.array(p90s),
        np.array(p95s),
    )


def main():
    parser = argparse.ArgumentParser(
        description="Bucket‐percentiles + Huber regression on plan_length vs. error"
    )
    parser.add_argument(
        "--task",
        choices=["time", "card"],
        default="time",
        help="Which error to use: 'time' → q_error; 'card' → q_card",
    )
    parser.add_argument(
        "--num_buckets",
        type=int,
        default=1,
        help="Number of equal‐width buckets to split plan_length into",
    )
    parser.add_argument(
        "--output_dir",
        default="bucket_plots",
        help="Directory to save the combined figures",
    )
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    if args.task == "time":
        workloads = ["tpch", "tpcds", "syn", "job", "job_full", "stats"]
    else:
        workloads = ["syn", "job", "job_full", "stats"]
    # workloads = ["tpch", "tpcds", "syn", "job", "stats"]

    for wl in workloads:
        suffix = "q_error" if args.task == "time" else "q_error"
        csv_file = (
            f"results/results_Train_{wl}_Test_{wl}_ours/"
            f"{args.task}_llm_pretrained-None_1.0_length_vs_qerror_postgres_"
            f"0.0001_b64_h2048_meta-llama-Llama-3.1-8B_emb1000_bucketize-separate_seed42.csv"
        )

        if not os.path.isfile(csv_file):
            print(f"[{wl}] File not found: {csv_file} → skipping")
            continue

        # Load
        df = pd.read_csv(csv_file)
        X = df[["plan_length"]].values.reshape(-1, 1)
        y = df[suffix].values

        # Compute bucket centers + percentiles
        bucket_centers, medians, p90s, p95s = compute_bucket_percentiles(
            plan_lengths=X,
            errors=y,
            num_buckets=args.num_buckets
        )

        # Save bucket data to file
        bucket_data = pd.DataFrame({
            'bucket_centers': bucket_centers.flatten(),
            'medians': medians,
            'p90s': p90s,
            'p95s': p95s
        })
        bucket_output_file = f"{wl}_{args.task}_{args.num_buckets}buckets_data.csv"
        bucket_output_path = os.path.join(args.output_dir, bucket_output_file)
        bucket_data.to_csv(bucket_output_path, index=False)
        print(f"[{wl}] Bucket data saved to: {bucket_output_path}")

        # Fit one Huber to the median points, and one to the 90th points
        huber_med = HuberRegressor()
        huber_med.fit(bucket_centers, medians)
        huber_p90 = HuberRegressor()
        huber_p90.fit(bucket_centers, p90s)
        huber_p95 = HuberRegressor()
        huber_p95.fit(bucket_centers, p95s)

        # For a smooth line, evaluate each Huber model on a fine grid
        x_line = np.linspace(
            bucket_centers.min(),
            bucket_centers.max(),
            200
        ).reshape(-1, 1)
        y_line_med = huber_med.predict(x_line)
        y_line_p90 = huber_p90.predict(x_line)
        y_line_p95 = huber_p95.predict(x_line)

        # Plot
        fig, ax = plt.subplots(figsize=(8, 5))

        # 1) Plot raw percentile‐points:
        ax.scatter(
            bucket_centers.flatten(),
            medians,
            s=50,
            color="tab:blue",
            marker="o",
            label="50th percentile"
        )
        ax.scatter(
            bucket_centers.flatten(),
            p90s,
            s=50,
            color="tab:orange",
            marker="s",
            label="90th percentile"
        )
        ax.scatter(
            bucket_centers.flatten(),
            p95s,
            s=50,
            color="tab:green",
            marker="s",
            label="95th percentile"
        )
        # 2) Plot Huber‐fitted lines
        ax.plot(
            x_line.flatten(),
            y_line_med,
            color="tab:blue",
            linestyle="-",
            linewidth=2.0,
            label="Huber fit (50th)"
        )
        ax.plot(
            x_line.flatten(),
            y_line_p90,
            color="tab:orange",
            linestyle="-",
            linewidth=2.0,
            label="Huber fit (90th)"
        )
        ax.plot(
            x_line.flatten(),
            y_line_p95,
            color="tab:green",
            linestyle="-",
            linewidth=2.0,
            label="Huber fit (95th)"
        )
        plt.tick_params(labelsize = 28)
        ax.set_xlabel("Plan Length",fontweight='bold',fontsize=28)
        ax.set_ylabel("Q-Error",fontweight='bold',fontsize=28)
        # ax.set_ylabel(suffix,fontweight='bold',fontsize=24)
        # ax.set_title(
        #     f"Plan‐length Buckets={args.num_buckets}  → 50%, 90% and 95% percentile with Huber Lines\n"
        #     f"Workload={wl}  |  Task={args.task}"
        # )
        ax.grid(True)
        # ax.legend(fontsize="xx-large", loc="upper left", framealpha=0.5,
        #             labelspacing=0.2,     # vertical spacing between items
        #             handletextpad=0.3,    # spacing between marker and text
        #             borderaxespad=0.3,    # spacing between legend and plot
        #             handlelength=1.0)
        ax.legend(
            loc="upper center",
            bbox_to_anchor=(0.5, 1.45),  # shift above the plot
            ncol=3,                      # 3 items per row
            fontsize="xx-large",
            framealpha=0.5,
            labelspacing=0.4,
            columnspacing=1.0,
            handletextpad=0.5,
            borderaxespad=0.2
        )


        # Optionally, clip the y‐axis (uncomment if desired):
        # ax.set_ylim(1, 3)

        out_file = f"{wl}_{args.task}_{args.num_buckets}buckets.png"
        out_path = os.path.join(args.output_dir, out_file)
        fig.tight_layout()
        if wl in ["job", "job_full", "stats"]:
            plt.ylim(0,6)
        else:
            plt.ylim(0.95,1.55)
            ax.set_yticks([1, 1.5])
        ax.xaxis.set_major_formatter(mticker.FuncFormatter(format_k))

        if wl=="tpch":
            ax.set_xticks([2000, 3000, 4000])
            ax.set_xticklabels(['2k', '3k', '4k'])

        fig.savefig(out_path, dpi=300, bbox_inches="tight")
        plt.close(fig)

        # Print model diagnostics (optional)
        r2_med = r2_score(medians, huber_med.predict(bucket_centers))
        r2_p90 = r2_score(p90s, huber_p90.predict(bucket_centers))
        r2_p95 = r2_score(p95s, huber_p95.predict(bucket_centers))
        print(
            f"[{wl}] 50th‐pct Huber slope={huber_med.coef_[0]:.6f},"
            f" intercept={huber_med.intercept_:.4f},  R²={r2_med:.4f}"
        )
        print(
            f"[{wl}] 90th‐pct Huber slope={huber_p90.coef_[0]:.6f},"
            f" intercept={huber_p90.intercept_:.4f},  R²={r2_p90:.4f}\n"
        )
        print(
            f"[{wl}] 95th‐pct Huber slope={huber_p95.coef_[0]:.6f},"
            f" intercept={huber_p95.intercept_:.4f},  R²={r2_p95:.4f}\n"
        )


if __name__ == "__main__":
    main()
