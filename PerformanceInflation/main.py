import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import matplotlib.pyplot as plt
import cpi

from config import RAWG_API_KEY, GAMES_LIMIT_PER_YEAR, CHOSEN_SERIES, generate_gpu_list
from passmark_adapter import fetch_passmark_scores, find_score
from rawg_adapter import fetch_rawg_requirements
from tpu_adapter import fetch_gpu_data

plt.style.use('dark_background')

def adjust_for_inflation(original_price, launch_year):
    try:
        adjusted_price = cpi.inflate(original_price, launch_year, to=2024)
        return round(adjusted_price, 2)
    except Exception:
        return original_price

def run_pipeline():
    if RAWG_API_KEY == "YOUR_API_KEY_HERE":
        print("ERROR: Configure your RAWG_API_KEY in config.py!")
        return

    passmark_dict = fetch_passmark_scores()
    gpu_names = generate_gpu_list(CHOSEN_SERIES)
    gpu_data = []
    
    print("\n[Hardware] Extracting Year and Price (MSRP) for each generation...")
    for name in gpu_names:
        specs = fetch_gpu_data(name)
        
        if specs and specs['year'] and specs['msrp']:
            year = specs['year']
            msrp_price = specs['msrp']
            gpu_data.append({'Year': year, 'GPU': name, 'MSRP': msrp_price})
            print(f"  -> {name} (Launched in {year} for ${msrp_price})")
        else:
            print(f"  [Warning] Skipping {name} due to data retrieval failure.")

    df = pd.DataFrame(gpu_data)
    
    if df.empty:
        print("\n[CRITICAL ERROR] GPU DataFrame is empty.")
        return
    
    dynamic_demand = []
    for year in df['Year'].unique():
        recommended_gpus = fetch_rawg_requirements(year, GAMES_LIMIT_PER_YEAR)
        year_scores = [find_score(gpu, passmark_dict) for gpu in recommended_gpus if find_score(gpu, passmark_dict)]
        avg_year_score = int(sum(year_scores) / len(year_scores)) if year_scores else 0
        dynamic_demand.append({'Year': year, 'Average_Demand': avg_year_score})
        print(f"  [AVERAGE {year}]: {avg_year_score} points required.")

    demand_df = pd.DataFrame(dynamic_demand)
    df = pd.merge(df, demand_df, on='Year', how='left')
    df = df[df['Average_Demand'] > 0]

    if df.empty:
        print("\n[CRITICAL ERROR] Processed DataFrame is empty.")
        return

    print(f"\n[Processing] Calculating graphical and financial inflation for Series {CHOSEN_SERIES}...")
    df['Raw_Power'] = df['GPU'].apply(lambda x: find_score(x, passmark_dict))
    df = df.dropna(subset=['Raw_Power'])

    initial_base_demand = df.iloc[0]['Average_Demand']
    df['Inflation_Factor'] = df['Average_Demand'] / initial_base_demand
    df['Adjusted_Power'] = df['Raw_Power'] / df['Inflation_Factor']

    df['Adjusted_Price'] = df.apply(lambda row: adjust_for_inflation(row['MSRP'], row['Year']), axis=1)
    
    df['Performance_Per_Dollar'] = (df['Raw_Power'] / df['Adjusted_Price']).round(2)

    print("\n--- FINAL RESULT ---")
    print(df[['GPU', 'Year', 'MSRP', 'Adjusted_Price', 'Average_Demand', 'Adjusted_Power', 'Raw_Power', 'Performance_Per_Dollar']].to_string(index=False))

    filename = f"performance_history_series_{CHOSEN_SERIES}.csv"
    df.to_csv(filename, index=False, sep=';', decimal=',')
    
    generate_chart(df, CHOSEN_SERIES)

def generate_chart(df, series):
    fig, (ax1, ax2) = plt.subplots(nrows=2, ncols=1, figsize=(14, 12), sharex=True)
    x_labels = df['GPU'] + '\n(' + df['Year'].astype(str) + ')'

    line1 = ax1.plot(x_labels, df['Raw_Power'], marker='^', color='#00ffcc', linewidth=3, markersize=8, label='Raw Hardware Power (PassMark)')
    line2 = ax1.plot(x_labels, df['Average_Demand'], marker='x', color='#ff3333', linewidth=2, linestyle='--', label='Avg. Recommended Requirements (Top AAA)')
    line3 = ax1.plot(x_labels, df['Adjusted_Power'], marker='o', color='#ffaa00', linewidth=4, markersize=9, label='Real Perceived Performance (Adjusted Power)')

    ax1.fill_between(x_labels, df['Adjusted_Power'], df['Raw_Power'], color='#00ffcc', alpha=0.1)

    ax1.set_ylabel('Score (PassMark G3D Mark)', fontweight='bold', fontsize=11, color='#eeeeee')
    ax1.tick_params(axis='y', labelcolor='#eeeeee')
    ax1.grid(True, linestyle=':', alpha=0.3)
    ax1.set_title(f'Performance vs. Game Engine Demand (Series {series})', fontsize=13, fontweight='bold', pad=15)
    
    lines_ax1 = line1 + line2 + line3
    labels_ax1 = [l.get_label() for l in lines_ax1]
    ax1.legend(lines_ax1, labels_ax1, loc='upper left', facecolor='#1a1a1a', edgecolor='none')

    money_color = '#2ecc71'
    line4 = ax2.plot(x_labels, df['Adjusted_Price'], marker='D', color=money_color, linestyle='-.', linewidth=2.5, markersize=8, label='Inflation-Adjusted Price (US$)')
    
    ax2.set_ylabel('Adjusted Price (Dollars)', fontweight='bold', fontsize=11, color=money_color)
    ax2.tick_params(axis='y', labelcolor=money_color)
    ax2.grid(True, linestyle=':', alpha=0.3)

    ax3 = ax2.twinx()
    ratio_color = '#bd93f9'
    line5 = ax3.plot(x_labels, df['Performance_Per_Dollar'], marker='s', color=ratio_color, linestyle=':', linewidth=2.5, markersize=8, label='Performance per Dollar (Score/$)')
    
    ax3.set_ylabel('Performance per Dollar (Score/US$)', fontweight='bold', fontsize=11, color=ratio_color)
    ax3.tick_params(axis='y', labelcolor=ratio_color)

    ax2.set_title('Hardware Economy: Price vs. Value', fontsize=13, fontweight='bold', pad=15)
    ax2.set_xlabel('GPU Generation', fontweight='bold', fontsize=11)

    lines_ax2 = line4 + line5
    labels_ax2 = [l.get_label() for l in lines_ax2]
    ax2.legend(lines_ax2, labels_ax2, loc='upper left', facecolor='#1a1a1a', edgecolor='none')

    fig.suptitle('Performance Inflation Dashboard', fontsize=16, fontweight='bold', y=0.98)
    fig.tight_layout()
    plt.subplots_adjust(top=0.92)
    plt.show()

if __name__ == "__main__":
    run_pipeline()