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
# 4b. COMBINED PLOTS — All three judges side by side, single legend
# ============================================================

JUDGE_LABELS = {
    "claude-sonnet-4-6": "Claude Sonnet 4.6",
    "gpt-4o": "GPT-4o",
    "gemini-2.5-flash-lite": "Gemini 2.5 Flash Lite",
}

JUDGE_ORDER = ["claude-sonnet-4-6", "gpt-4o", "gemini-2.5-flash-lite"]

ROLE_COLORS = {"Mafia": "#d62728", "Doctor": "#2ca02c", "Villager": "#1f77b4"}


def _bootstrap_ci(data, n_boot=5000, ci=95, seed=42):
    """Return (mean, lower, upper) using bootstrap resampling."""
    rng = np.random.default_rng(seed)
    means = [np.mean(rng.choice(data, size=len(data), replace=True)) for _ in range(n_boot)]
    lo = np.percentile(means, (100 - ci) / 2)
    hi = np.percentile(means, 100 - (100 - ci) / 2)
    return np.mean(data), lo, hi


def plot_dimension_breakdown(df, outdir):
    """Grouped bar chart with 95% bootstrap CI error bars, by Mafia behavioral level."""
    dims = ["direct_contradiction", "strategic_omission", "fabrication", "misdirection", "overall_deception"]
    dim_labels = {
        "direct_contradiction": "Direct\nContradiction",
        "strategic_omission": "Strategic\nOmission",
        "fabrication": "Fabrication",
        "misdirection": "Misdirection",
        "overall_deception": "Overall\nDeception",
    }

    mafia = df[df["agent_role"] == "Mafia"]
    levels = sorted(mafia["mafia_level"].unique())

    # Precompute bootstrap CIs for every (level, dim) cell
    ci_data = {}
    for lvl in levels:
        sub = mafia[mafia["mafia_level"] == lvl]
        ci_data[lvl] = {}
        for d in dims:
            mean, lo, hi = _bootstrap_ci(sub[d].values)
            ci_data[lvl][d] = (mean, lo, hi)

    x = np.arange(len(dims))
    n_levels = len(levels)
    width = 0.18
    colors = ["#d4e6f1", "#85c1e9", "#2e86c1", "#1a5276"]

    fig, ax = plt.subplots(figsize=(12, 5.5))

    for i, lvl in enumerate(levels):
        offset = (i - n_levels / 2 + 0.5) * width
        means = [ci_data[lvl][d][0] for d in dims]
        errs_lo = [ci_data[lvl][d][0] - ci_data[lvl][d][1] for d in dims]
        errs_hi = [ci_data[lvl][d][2] - ci_data[lvl][d][0] for d in dims]
        ax.bar(x + offset, means, width, label=f"Level {lvl}",
               color=colors[i], edgecolor="black", linewidth=0.5)
        ax.errorbar(x + offset, means,
                    yerr=[errs_lo, errs_hi],
                    fmt="none", color="black", capsize=3, linewidth=1)

    ax.set_xticks(x)
    ax.set_xticklabels([dim_labels[d] for d in dims], fontsize=10)
    ax.set_ylabel("Mean Score (0–10)", fontsize=11)
    ax.set_ylim(0, 10.5)
    ax.set_title("Deception Dimension Breakdown by Mafia Behavioral Level\n"
                 "(averaged across all judges; error bars = 95% bootstrap CI)",
                 fontsize=12, fontweight="bold")
    ax.legend(title="Mafia Level", fontsize=9, title_fontsize=9)
    ax.axhline(y=7, color="red", linestyle="--", alpha=0.4, linewidth=1)
    ax.text(4.62, 7.1, "floor (~7)", color="red", fontsize=8, alpha=0.7)

    plt.tight_layout()
    fname = "dimension_breakdown.png"
    fig.savefig(os.path.join(outdir, fname), dpi=DPI, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {fname}")


def plot_deception_radar_combined(df, outdir):
    """Radar chart with all judges side by side and a single shared legend."""
    dims = ["direct_contradiction", "strategic_omission", "fabrication", "misdirection"]
    dim_labels = ["Direct\nContradiction", "Strategic\nOmission", "Fabrication", "Misdirection"]
    roles = ["Mafia", "Doctor", "Villager"]

    judges = [j for j in JUDGE_ORDER if j in df["judge_model"].unique()]
    n = len(judges)
    fig, axes = plt.subplots(1, n, figsize=(6 * n, 6), subplot_kw=dict(polar=True))
    if n == 1:
        axes = [axes]

    angles = np.linspace(0, 2 * np.pi, len(dims), endpoint=False).tolist()
    angles += angles[:1]

    legend_handles = []
    for ax, judge in zip(axes, judges):
        jdf = df[df["judge_model"] == judge]
        for role in roles:
            role_df = jdf[jdf["agent_role"] == role]
            if role_df.empty:
                continue
            values = [role_df[d].mean() for d in dims]
            values += values[:1]
            line, = ax.plot(angles, values, 'o-', linewidth=2, label=role, color=ROLE_COLORS[role])
            ax.fill(angles, values, alpha=0.15, color=ROLE_COLORS[role])
            if ax is axes[0]:
                legend_handles.append(line)

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(dim_labels, fontsize=9)
        ax.set_ylim(0, 10)
        ax.set_title(JUDGE_LABELS.get(judge, judge), fontsize=11, fontweight="bold", pad=20)

    fig.suptitle("Deception Profile by Role — All Judges", fontsize=14, fontweight="bold", y=1.02)
    fig.legend(handles=legend_handles, labels=roles, loc="lower center",
               ncol=3, fontsize=11, bbox_to_anchor=(0.5, -0.08))
    plt.subplots_adjust(bottom=0.12)

    plt.tight_layout()
    fname = "radar_combined.png"
    fig.savefig(os.path.join(outdir, fname), dpi=DPI, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {fname}")


def plot_deception_floor_combined(df, outdir):
    """Violin plots for all judges side by side with a single shared legend."""
    judges = [j for j in JUDGE_ORDER if j in df["judge_model"].unique()]
    n = len(judges)
    fig, axes = plt.subplots(1, n, figsize=(6 * n, 5), sharey=True)
    if n == 1:
        axes = [axes]

    for ax, judge in zip(axes, judges):
        jdf = df[df["judge_model"] == judge]
        mafia_l1 = jdf[(jdf["agent_role"] == "Mafia") & (jdf["mafia_level"] == 1)]

        sns.violinplot(data=mafia_l1, x="doc_level", y="overall_deception",
                       inner="box", palette="YlOrRd", ax=ax, cut=0)
        mean_val = mafia_l1["overall_deception"].mean()
        ax.axhline(y=mean_val, color="red", linestyle="--", alpha=0.7)
        ax.set_title(JUDGE_LABELS.get(judge, judge), fontsize=11, fontweight="bold")
        ax.set_xlabel("Doctor Behavioral Level", fontsize=10)
        ax.set_ylim(0, 10.5)
        ax.text(0.97, mean_val + 0.15, f"Mean: {mean_val:.1f}",
                transform=ax.get_yaxis_transform(), ha="right", color="red", fontsize=9)

    axes[0].set_ylabel("Overall Deception Score", fontsize=11)
    for ax in axes[1:]:
        ax.set_ylabel("")

    fig.suptitle("Deception Floor: Mafia at Level 1 (Complete Honesty) — All Judges",
                 fontsize=13, fontweight="bold")
    plt.tight_layout()
    fname = "deception_floor_combined.png"
    fig.savefig(os.path.join(outdir, fname), dpi=DPI, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {fname}")


def plot_role_comparison_combined(df, outdir):
    """Box plots by role for all judges side by side with a single shared legend."""
    judges = [j for j in JUDGE_ORDER if j in df["judge_model"].unique()]
    n = len(judges)
    order = ["Mafia", "Doctor", "Villager"]
    palette = ROLE_COLORS

    fig, axes = plt.subplots(1, n, figsize=(6 * n, 5), sharey=True)
    if n == 1:
        axes = [axes]

    for ax, judge in zip(axes, judges):
        jdf = df[df["judge_model"] == judge]
        existing = [r for r in order if r in jdf["agent_role"].values]

        sns.boxplot(data=jdf, x="agent_role", y="overall_deception",
                    order=existing, palette=palette, ax=ax)
        sns.stripplot(data=jdf, x="agent_role", y="overall_deception",
                      order=existing, color="black", alpha=0.15, size=3, ax=ax)

        for i, role in enumerate(existing):
            mean_val = jdf[jdf["agent_role"] == role]["overall_deception"].mean()
            ax.annotate(f"μ={mean_val:.1f}", xy=(i, mean_val), fontsize=9,
                        ha="center", va="bottom", color="red", fontweight="bold")

        ax.set_title(JUDGE_LABELS.get(judge, judge), fontsize=11, fontweight="bold")
        ax.set_xlabel("Agent Role", fontsize=10)
        ax.set_ylim(0, 10.5)

    axes[0].set_ylabel("Overall Deception Score", fontsize=11)
    for ax in axes[1:]:
        ax.set_ylabel("")

    fig.suptitle("Deception by Role (All Configurations) — All Judges",
                 fontsize=13, fontweight="bold")
    plt.tight_layout()
    fname = "role_comparison_combined.png"
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
    """Aggregated config-level pairwise scatter (32 cells)."""
    available = df["judge_model"].unique()
    if len(available) < 2:
        print("  Skipping judge agreement (need 2+ judges)")
        return

    agg = df.groupby(["mafia_level", "doc_level", "agent_role", "judge_model"])["overall_deception"].mean().reset_index()
    pivot = agg.pivot_table(values="overall_deception",
                            index=["mafia_level", "doc_level", "agent_role"],
                            columns="judge_model").dropna()

    if pivot.shape[1] < 2:
        print("  Not enough overlapping data for judge comparison")
        return

    judge_list = [j for j in JUDGE_ORDER if j in pivot.columns]
    n_pairs = len(judge_list) * (len(judge_list) - 1) // 2
    pairs = [(judge_list[i], judge_list[j])
             for i in range(len(judge_list)) for j in range(i + 1, len(judge_list))]

    fig, axes = plt.subplots(1, n_pairs, figsize=(6 * n_pairs, 5.5))
    if n_pairs == 1:
        axes = [axes]

    for ax, (j1, j2) in zip(axes, pairs):
        ax.scatter(pivot[j1], pivot[j2], alpha=0.7, edgecolors="black", linewidth=0.5, s=50)
        ax.plot([0, 10], [0, 10], "r--", alpha=0.4, label="Perfect agreement")
        r = pivot[j1].corr(pivot[j2])
        ax.set_title(f"r = {r:.3f}", fontsize=12, fontweight="bold")
        ax.set_xlabel(JUDGE_LABELS.get(j1, j1), fontsize=10)
        ax.set_ylabel(JUDGE_LABELS.get(j2, j2), fontsize=10)
        ax.set_xlim(0, 10.5)
        ax.set_ylim(0, 10.5)
        ax.set_aspect("equal")
        ax.legend(fontsize=9)

    fig.suptitle("Cross-Judge Agreement — Config-Level Means (n=32 cells)",
                 fontsize=13, fontweight="bold")
    plt.tight_layout()
    fname = "judge_agreement_aggregated.png"
    fig.savefig(os.path.join(outdir, fname), dpi=DPI, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {fname}")


def plot_judge_agreement_individual(df, outdir):
    """Individual game-level pairwise scatter colored by role, with ICC and Krippendorff alpha."""
    import pingouin as pg
    import krippendorff as ka

    judges = df["judge_model"].unique()
    if len(judges) < 2:
        return

    pivot = df.pivot_table(values="overall_deception",
                           index=["game_folder", "agent_name", "agent_role"],
                           columns="judge_model").dropna().reset_index()

    judge_list = [j for j in JUDGE_ORDER if j in pivot.columns]
    n_pairs = len(judge_list) * (len(judge_list) - 1) // 2
    pairs = [(judge_list[i], judge_list[j])
             for i in range(len(judge_list)) for j in range(i + 1, len(judge_list))]

    # Compute ICC and Krippendorff alpha
    long = pivot[["game_folder", "agent_name"] + judge_list].melt(
        id_vars=["game_folder", "agent_name"], value_vars=judge_list,
        var_name="rater", value_name="score")
    long["target"] = long["game_folder"] + "_" + long["agent_name"]
    icc_df = pg.intraclass_corr(data=long, targets="target", raters="rater", ratings="score")
    icc_val = icc_df[icc_df["Type"] == "ICC(A,1)"]["ICC"].values[0]
    ci = icc_df[icc_df["Type"] == "ICC(A,1)"]["CI95"].values[0]
    alpha_val = ka.alpha(reliability_data=pivot[judge_list].values.T,
                         level_of_measurement="interval")

    fig, axes = plt.subplots(1, n_pairs, figsize=(6 * n_pairs, 5.5))
    if n_pairs == 1:
        axes = [axes]

    for ax, (j1, j2) in zip(axes, pairs):
        for role, color in ROLE_COLORS.items():
            sub = pivot[pivot["agent_role"] == role]
            r = sub[j1].corr(sub[j2])
            ax.scatter(sub[j1], sub[j2], color=color, alpha=0.4,
                       edgecolors="black", linewidth=0.3, s=25,
                       label=f"{role} (r={r:.2f})")
        ax.plot([0, 10], [0, 10], "r--", alpha=0.4)
        ax.set_xlabel(JUDGE_LABELS.get(j1, j1), fontsize=10)
        ax.set_ylabel(JUDGE_LABELS.get(j2, j2), fontsize=10)
        ax.set_xlim(0, 10.5)
        ax.set_ylim(0, 10.5)
        ax.set_aspect("equal")
        ax.legend(fontsize=8, loc="upper left")

    fig.suptitle(
        f"Cross-Judge Agreement — Individual Game Scores (n≈670)\n"
        f"ICC(A,1) = {icc_val:.3f}  95% CI [{ci[0]:.2f}, {ci[1]:.2f}]    Krippendorff α = {alpha_val:.3f}",
        fontsize=12, fontweight="bold"
    )
    plt.tight_layout()
    fname = "judge_agreement_individual.png"
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

    print("\n--- Combined Plots (all judges) ---")
    plot_deception_radar_combined(df, args.outdir)
    plot_deception_floor_combined(df, args.outdir)
    plot_role_comparison_combined(df, args.outdir)

    print("\n--- Win Rate Analysis ---")
    plot_win_rates(df, args.outdir)

    print("\n--- Cross-Judge Agreement ---")
    plot_judge_agreement(df, args.outdir)
    plot_judge_agreement_individual(df, args.outdir)

    print("\n--- Summary Statistics ---")
    print_summary_stats(df, args.outdir)

    print(f"\nAll plots saved to: {args.outdir}/")


if __name__ == "__main__":
    main()