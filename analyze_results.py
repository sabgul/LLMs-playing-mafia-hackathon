"""
Analysis and plotting script for LLM-Mafia experiments.
Reads judge_results.csv and produces publication-ready plots.

Usage:
  python analyze_results.py

  # Only plot results from a specific judge
  python analyze_results.py --judge claude-sonnet-4-6

  # Save plots to a specific directory
  python analyze_results.py --outdir figures

Requires: pip install pandas matplotlib seaborn numpy
"""

import os
import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.gridspec import GridSpec

# Style
sns.set_theme(style="whitegrid", font_scale=1.1)
CMAP = "YlOrRd"
FIGSIZE_HEATMAP = (7, 5.5)
FIGSIZE_WIDE = (14, 5.5)
DPI = 200


def load_data(csv_path="judge_results.csv", judge_filter=None):
    df = pd.read_csv(csv_path)
    if judge_filter:
        df = df[df["judge_model"] == judge_filter]
    print(f"Loaded {len(df)} rows from {csv_path}")
    print(f"Judges: {df['judge_model'].unique()}")
    print(f"Configs: {df[['mafia_level','doc_level']].drop_duplicates().shape[0]}")
    print(f"Games: {df['game_folder'].nunique()}")
    return df


# ============================================================
# 1. HEATMAPS — Core deception scores by config
# ============================================================

def plot_heatmaps_by_role(df, role, score_col, title_prefix, outdir, judge_name=""):
    """Single heatmap for a given role and score column."""
    role_df = df[df["agent_role"] == role]
    pivot = role_df.pivot_table(values=score_col, index="mafia_level", columns="doc_level", aggfunc="mean")
    pivot_std = role_df.pivot_table(values=score_col, index="mafia_level", columns="doc_level", aggfunc="std")

    fig, ax = plt.subplots(figsize=FIGSIZE_HEATMAP)

    # Annotate with mean ± std
    annot = pivot.round(1).astype(str) + "\n±" + pivot_std.round(1).astype(str)

    sns.heatmap(pivot, annot=annot, fmt="", cmap=CMAP, vmin=0, vmax=10,
                cbar_kws={"label": "Deception Score"}, ax=ax, linewidths=0.5)

    ax.set_xlabel("Doctor Behavioral Level", fontsize=12)
    ax.set_ylabel("Mafia Behavioral Level", fontsize=12)
    ax.set_title(f"{title_prefix} — {role}\n{judge_name}", fontsize=13, fontweight="bold")
    ax.set_xticklabels([f"D-Lvl {i}" for i in pivot.columns])
    ax.set_yticklabels([f"M-Lvl {i}" for i in pivot.index], rotation=0)

    plt.tight_layout()
    fname = f"heatmap_{role.lower()}_{score_col}_{judge_name.replace(' ','_').replace('/','_')}.png"
    fig.savefig(os.path.join(outdir, fname), dpi=DPI, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {fname}")


def plot_all_heatmaps(df, outdir):
    """Generate heatmaps for each judge × role × score dimension."""
    score_cols = ["overall_deception", "direct_contradiction", "strategic_omission", "fabrication", "misdirection"]

    for judge in df["judge_model"].unique():
        jdf = df[df["judge_model"] == judge]
        for score in score_cols:
            plot_heatmaps_by_role(jdf, "Mafia", score, f"Average {score.replace('_',' ').title()}", outdir, judge)
            plot_heatmaps_by_role(jdf, "Doctor", score, f"Average {score.replace('_',' ').title()}", outdir, judge)


# ============================================================
# 2. DECEPTION FLOOR — Distribution at Level 1
# ============================================================

def plot_deception_floor(df, outdir):
    """Box/violin plot showing Mafia deception distribution at honesty level 1."""
    for judge in df["judge_model"].unique():
        jdf = df[df["judge_model"] == judge]
        mafia_l1 = jdf[(jdf["agent_role"] == "Mafia") & (jdf["mafia_level"] == 1)]

        fig, ax = plt.subplots(figsize=(8, 5))
        sns.violinplot(data=mafia_l1, x="doc_level", y="overall_deception",
                       inner="box", palette="YlOrRd", ax=ax, cut=0)

        ax.set_xlabel("Doctor Behavioral Level", fontsize=12)
        ax.set_ylabel("Overall Deception Score", fontsize=12)
        ax.set_title(f"Deception Floor: Mafia at Level 1 (Complete Honesty)\nJudge: {judge}",
                     fontsize=13, fontweight="bold")
        ax.set_ylim(0, 10.5)
        ax.axhline(y=mafia_l1["overall_deception"].mean(), color="red", linestyle="--",
                   alpha=0.7, label=f"Mean: {mafia_l1['overall_deception'].mean():.1f}")
        ax.legend()

        plt.tight_layout()
        fname = f"deception_floor_{judge.replace('/','_')}.png"
        fig.savefig(os.path.join(outdir, fname), dpi=DPI, bbox_inches="tight")
        plt.close()
        print(f"  Saved: {fname}")


# ============================================================
# 3. ROLE COMPARISON — Deception by role across all configs
# ============================================================

def plot_role_comparison(df, outdir):
    """Grouped box plot: deception by role, collapsed across configs."""
    for judge in df["judge_model"].unique():
        jdf = df[df["judge_model"] == judge]

        fig, ax = plt.subplots(figsize=(9, 5))
        order = ["Mafia", "Doctor", "Villager"]
        existing_roles = [r for r in order if r in jdf["agent_role"].values]

        sns.boxplot(data=jdf, x="agent_role", y="overall_deception",
                    order=existing_roles, palette="Set2", ax=ax)
        sns.stripplot(data=jdf, x="agent_role", y="overall_deception",
                      order=existing_roles, color="black", alpha=0.15, size=3, ax=ax)

        ax.set_xlabel("Agent Role", fontsize=12)
        ax.set_ylabel("Overall Deception Score", fontsize=12)
        ax.set_title(f"Deception by Role (All Configurations)\nJudge: {judge}",
                     fontsize=13, fontweight="bold")
        ax.set_ylim(0, 10.5)

        # Add means
        for i, role in enumerate(existing_roles):
            mean_val = jdf[jdf["agent_role"] == role]["overall_deception"].mean()
            ax.annotate(f"μ={mean_val:.1f}", xy=(i, mean_val), fontsize=10,
                        ha="center", va="bottom", color="red", fontweight="bold")

        plt.tight_layout()
        fname = f"role_comparison_{judge.replace('/','_')}.png"
        fig.savefig(os.path.join(outdir, fname), dpi=DPI, bbox_inches="tight")
        plt.close()
        print(f"  Saved: {fname}")


# ============================================================
# 4. SUB-DIMENSION RADAR — What kinds of deception do roles use?
# ============================================================

def plot_deception_radar(df, outdir):
    """Radar chart comparing deception sub-dimensions by role."""
    dims = ["direct_contradiction", "strategic_omission", "fabrication", "misdirection"]
    dim_labels = ["Direct\nContradiction", "Strategic\nOmission", "Fabrication", "Misdirection"]

    for judge in df["judge_model"].unique():
        jdf = df[df["judge_model"] == judge]

        fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True))
        angles = np.linspace(0, 2 * np.pi, len(dims), endpoint=False).tolist()
        angles += angles[:1]  # close the polygon

        colors = {"Mafia": "#d62728", "Doctor": "#2ca02c", "Villager": "#1f77b4"}

        for role in ["Mafia", "Doctor", "Villager"]:
            role_df = jdf[jdf["agent_role"] == role]
            if role_df.empty:
                continue
            values = [role_df[d].mean() for d in dims]
            values += values[:1]
            ax.plot(angles, values, 'o-', linewidth=2, label=role, color=colors.get(role, "gray"))
            ax.fill(angles, values, alpha=0.15, color=colors.get(role, "gray"))

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(dim_labels, fontsize=10)
        ax.set_ylim(0, 10)
        ax.set_title(f"Deception Profile by Role\nJudge: {judge}", fontsize=13, fontweight="bold", pad=20)
        ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1))

        plt.tight_layout()
        fname = f"radar_{judge.replace('/','_')}.png"
        fig.savefig(os.path.join(outdir, fname), dpi=DPI, bbox_inches="tight")
        plt.close()
        print(f"  Saved: {fname}")


# ============================================================
# 5. WIN RATE ANALYSIS
# ============================================================

def plot_win_rates(df, outdir):
    """Heatmap of Mafia win rate by config."""
    for judge in df["judge_model"].unique():
        jdf = df[df["judge_model"] == judge]

        # One row per game (not per agent)
        games = jdf.drop_duplicates(subset=["game_folder"])
        games["mafia_win"] = (games["winner"].str.lower() == "mafia").astype(int)

        pivot = games.pivot_table(values="mafia_win", index="mafia_level",
                                  columns="doc_level", aggfunc="mean")

        fig, ax = plt.subplots(figsize=FIGSIZE_HEATMAP)
        sns.heatmap(pivot, annot=True, fmt=".0%", cmap="RdYlGn_r", vmin=0, vmax=1,
                    cbar_kws={"label": "Mafia Win Rate"}, ax=ax, linewidths=0.5)

        ax.set_xlabel("Doctor Behavioral Level", fontsize=12)
        ax.set_ylabel("Mafia Behavioral Level", fontsize=12)
        ax.set_title(f"Mafia Win Rate by Configuration\nJudge: {judge}",
                     fontsize=13, fontweight="bold")
        ax.set_xticklabels([f"D-Lvl {i}" for i in pivot.columns])
        ax.set_yticklabels([f"M-Lvl {i}" for i in pivot.index], rotation=0)

        plt.tight_layout()
        fname = f"winrate_{judge.replace('/','_')}.png"
        fig.savefig(os.path.join(outdir, fname), dpi=DPI, bbox_inches="tight")
        plt.close()
        print(f"  Saved: {fname}")


# ============================================================
# 6. CROSS-JUDGE AGREEMENT
# ============================================================

def plot_judge_agreement(df, outdir):
    """Compare overall deception scores across different judges."""
    judges = df["judge_model"].unique()
    if len(judges) < 2:
        print("  Skipping judge agreement (need 2+ judges)")
        return

    # Aggregate: mean overall_deception per (config, role, agent) across judges
    agg = df.groupby(["mafia_level", "doc_level", "agent_role", "judge_model"])["overall_deception"].mean().reset_index()

    # Pivot so each judge is a column
    pivot = agg.pivot_table(values="overall_deception",
                            index=["mafia_level", "doc_level", "agent_role"],
                            columns="judge_model").dropna()

    if pivot.shape[1] < 2:
        print("  Not enough overlapping data for judge comparison")
        return

    # Pairwise scatter plots
    judge_list = list(pivot.columns)
    n_pairs = len(judge_list) * (len(judge_list) - 1) // 2

    fig, axes = plt.subplots(1, n_pairs, figsize=(6 * n_pairs, 5.5))
    if n_pairs == 1:
        axes = [axes]

    pair_idx = 0
    for i in range(len(judge_list)):
        for j in range(i + 1, len(judge_list)):
            ax = axes[pair_idx]
            j1, j2 = judge_list[i], judge_list[j]

            ax.scatter(pivot[j1], pivot[j2], alpha=0.6, edgecolors="black", linewidth=0.5, s=40)
            ax.plot([0, 10], [0, 10], "r--", alpha=0.5, label="Perfect agreement")

            corr = pivot[j1].corr(pivot[j2])
            ax.set_xlabel(j1, fontsize=10)
            ax.set_ylabel(j2, fontsize=10)
            ax.set_title(f"r = {corr:.3f}", fontsize=12, fontweight="bold")
            ax.set_xlim(0, 10.5)
            ax.set_ylim(0, 10.5)
            ax.set_aspect("equal")
            ax.legend(fontsize=9)

            pair_idx += 1

    fig.suptitle("Cross-Judge Agreement on Overall Deception", fontsize=14, fontweight="bold")
    plt.tight_layout()
    fname = "judge_agreement.png"
    fig.savefig(os.path.join(outdir, fname), dpi=DPI, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {fname}")


# ============================================================
# 7. SUMMARY STATISTICS TABLE
# ============================================================

def print_summary_stats(df, outdir):
    """Print and save key summary statistics."""
    lines = []
    lines.append("=" * 70)
    lines.append("SUMMARY STATISTICS")
    lines.append("=" * 70)

    for judge in df["judge_model"].unique():
        jdf = df[df["judge_model"] == judge]
        lines.append(f"\nJudge: {judge}")
        lines.append("-" * 50)

        for role in ["Mafia", "Doctor", "Villager"]:
            rdf = jdf[jdf["agent_role"] == role]
            if rdf.empty:
                continue
            lines.append(f"\n  {role}:")
            lines.append(f"    Overall Deception:     {rdf['overall_deception'].mean():.2f} ± {rdf['overall_deception'].std():.2f}")
            lines.append(f"    Direct Contradiction:  {rdf['direct_contradiction'].mean():.2f} ± {rdf['direct_contradiction'].std():.2f}")
            lines.append(f"    Strategic Omission:     {rdf['strategic_omission'].mean():.2f} ± {rdf['strategic_omission'].std():.2f}")
            lines.append(f"    Fabrication:            {rdf['fabrication'].mean():.2f} ± {rdf['fabrication'].std():.2f}")
            lines.append(f"    Misdirection:           {rdf['misdirection'].mean():.2f} ± {rdf['misdirection'].std():.2f}")

        # Deception floor
        mafia_l1 = jdf[(jdf["agent_role"] == "Mafia") & (jdf["mafia_level"] == 1)]
        if not mafia_l1.empty:
            lines.append(f"\n  DECEPTION FLOOR (Mafia at Level 1):")
            lines.append(f"    Mean: {mafia_l1['overall_deception'].mean():.2f} ± {mafia_l1['overall_deception'].std():.2f}")
            lines.append(f"    Min:  {mafia_l1['overall_deception'].min():.1f}")
            lines.append(f"    Max:  {mafia_l1['overall_deception'].max():.1f}")

        # Win rates
        games = jdf.drop_duplicates(subset=["game_folder"])
        mafia_wins = (games["winner"].str.lower() == "mafia").mean()
        lines.append(f"\n  Overall Mafia Win Rate: {mafia_wins:.1%}")

    output = "\n".join(lines)
    print(output)

    with open(os.path.join(outdir, "summary_stats.txt"), "w") as f:
        f.write(output)
    print(f"\n  Saved: summary_stats.txt")


# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Analyze LLM-Mafia judge results")
    parser.add_argument("--csv", default="judge_results.csv", help="Path to results CSV")
    parser.add_argument("--judge", type=str, help="Filter to specific judge model")
    parser.add_argument("--outdir", default="figures", help="Output directory for plots")
    args = parser.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    df = load_data(args.csv, args.judge)

    if df.empty:
        print("No data to analyze!")
        return

    print("\n--- Generating Heatmaps ---")
    plot_all_heatmaps(df, args.outdir)

    print("\n--- Deception Floor Distribution ---")
    plot_deception_floor(df, args.outdir)

    print("\n--- Role Comparison ---")
    plot_role_comparison(df, args.outdir)

    print("\n--- Deception Radar Charts ---")
    plot_deception_radar(df, args.outdir)

    print("\n--- Win Rate Analysis ---")
    plot_win_rates(df, args.outdir)

    print("\n--- Cross-Judge Agreement ---")
    plot_judge_agreement(df, args.outdir)

    print("\n--- Summary Statistics ---")
    print_summary_stats(df, args.outdir)

    print(f"\nAll plots saved to: {args.outdir}/")


if __name__ == "__main__":
    main()