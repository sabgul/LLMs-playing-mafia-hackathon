import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

# 1. Organize your averaged results into a matrix
# Rows = Mafia Levels (1-4), Columns = Doctor Levels (1-4)
data_no_api_errors_mafia = [
    [8.5, 8.5, 8.5, 9],  # Mafia Level 1 results
    [9, 9, 9, 9],  # Mafia Level 2 results
    [8.5, 9, 8.5, 9],  # Mafia Level 3 results
    [8.5, 9, 8.5, 9]   # Mafia Level 4 results
]

data_no_api_errors_doctor = [
    [4, 6, 6, 7],  # Mafia Level 1
    [5, 4, 3, 3],  # Mafia Level 2
    [2, 8, 3, 7],  # Mafia Level 3
    [3, 7, 6, 7]   # Mafia Level 4
]

data_api_errors_mafia = [
    [7.5, 9, 9.5, 9],  # Mafia Level 1 results
    [9, 9.5, 9, 8.5],  # Mafia Level 2 results
    [8.5, 10, 8.5, 9],  # Mafia Level 3 results
    [7.5, 8.5, 8.5, 9]   # Mafia Level 4 results
]

data_api_errors_doctor = [
    [5, 8, 5, 1],  # Mafia Level 1
    [6, 6, 9, 3],  # Mafia Level 2
    [2, 2, 7, 7],  # Mafia Level 3
    [6, 1, 7, 4]   # Mafia Level 4
]

if __name__ == "__main__":
    df = pd.DataFrame(data_api_errors_doctor,
                      index=[f"M-Lvl {i}" for i in range(1,5)],
                      columns=[f"D-Lvl {i}" for i in range(1,5)])

    # --- PLOT 1: HEATMAP ---
    plt.figure(figsize=(8, 6))
    sns.heatmap(df, annot=True, cmap="YlOrRd", fmt=".1f", cbar_kws={'label': 'Deception Score'})
    plt.title("Heatmap: Average Doctor Deception Score per Configuration with API err")
    plt.xlabel("Doctor Behavioral Level")
    plt.ylabel("Mafia Behavioral Level")
    plt.savefig("deception_heatmap_doctor_api_err.png")

    # --- PLOT 2: GROUPED BAR CHART ---
    df_melted = df.reset_index().melt(id_vars='index')
    df_melted.columns = ['Mafia_Level', 'Doctor_Level', 'Score']

    plt.figure(figsize=(10, 6))
    sns.barplot(data=df_melted, x='Mafia_Level', y='Score', hue='Doctor_Level')
    plt.title("Deception Trends Across Behavioral Levels")
    plt.ylabel("Deception Score (0-10)")
    plt.legend(title="Doctor Level", bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig("deception_barplot.png")