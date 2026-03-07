import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import matplotlib.pyplot as plt
import cpi
import tkinter as tk

from config import RAWG_API_KEY, GAMES_LIMIT_PER_YEAR, CHOSEN_SERIES, generate_gpu_list, generate_competitor_list
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

def prompt_visualization_choice():
    choice = ['1']
    root = tk.Tk()
    root.title("Select Dashboard")
    root.geometry("350x150")
    
    try:
        root.eval('tk::PlaceWindow . center')
    except Exception:
        pass

    def select(option):
        choice[0] = option
        root.destroy()

    label = tk.Label(root, text="Choose the visualization mode:", font=("Arial", 12))
    label.pack(pady=15)

    btn1 = tk.Button(root, text="Classic View (NVIDIA Only)", width=30, command=lambda: select('1'))
    btn1.pack(pady=5)

    btn2 = tk.Button(root, text="Extended View (NVIDIA vs AMD)", width=30, command=lambda: select('2'))
    btn2.pack(pady=5)

    root.mainloop()
    return choice[0]

def run_pipeline():
    if RAWG_API_KEY == "YOUR_API_KEY_HERE":
        print("ERROR: Configure your RAWG_API_KEY in config.py!")
        return

    passmark_dict = fetch_passmark_scores()
    gpu_names = generate_gpu_list(CHOSEN_SERIES)
    amd_names = generate_competitor_list(CHOSEN_SERIES)
    gpu_data = []
    
    print("\n[Hardware] Extracting Year and Launch Price for each generation...")
    for i, name in enumerate(gpu_names):
        specs = fetch_gpu_data(name)
        
        if specs and specs['year'] and specs['msrp']:
            year = specs['year']
            msrp_price = specs['msrp']
            
            amd_name = amd_names[i] if i < len(amd_names) else None
            amd_msrp = None
            if amd_name:
                amd_specs = fetch_gpu_data(amd_name)
                if amd_specs and amd_specs['msrp']:
                    amd_msrp = amd_specs['msrp']

            gpu_data.append({
                'Year': year, 
                'GPU': name, 
                'MSRP': msrp_price,
                'AMD_GPU': amd_name,
                'AMD_MSRP': amd_msrp
            })
            print(f"  -> NVIDIA: {name} (${msrp_price}) vs AMD: {amd_name} (${amd_msrp})")
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
    df['AMD_Raw_Power'] = df['AMD_GPU'].apply(lambda x: find_score(x, passmark_dict) if pd.notnull(x) else None)
    df = df.dropna(subset=['Raw_Power'])

    initial_base_demand = df.iloc[0]['Average_Demand']
    df['Inflation_Factor'] = df['Average_Demand'] / initial_base_demand
    df['Adjusted_Power'] = df['Raw_Power'] / df['Inflation_Factor']

    df['Adjusted_Price'] = df.apply(lambda row: adjust_for_inflation(row['MSRP'], row['Year']), axis=1)
    df['Performance_Per_Dollar'] = (df['Raw_Power'] / df['Adjusted_Price']).round(2)
    
    df['AMD_Adjusted_Price'] = df.apply(lambda row: adjust_for_inflation(row['AMD_MSRP'], row['Year']) if pd.notnull(row['AMD_MSRP']) else None, axis=1)
    df['AMD_Perf_Per_Dollar'] = (df['AMD_Raw_Power'] / df['AMD_Adjusted_Price']).round(2)

    print("\n--- FINAL RESULT ---")
    print(df[['GPU', 'Year', 'MSRP', 'Adjusted_Price', 'Average_Demand', 'Adjusted_Power', 'Raw_Power', 'Performance_Per_Dollar']].to_string(index=False))

    filename = f"performance_history_series_{CHOSEN_SERIES}.csv"
    df.to_csv(filename, index=False, sep=';', decimal=',')
    
    choice = prompt_visualization_choice()
    
    if choice == '1':
        generate_classic_chart(df, CHOSEN_SERIES)
    else:
        generate_extended_charts(df, CHOSEN_SERIES)

def generate_classic_chart(df, series):
    fig, (ax1, ax2) = plt.subplots(nrows=2, ncols=1, figsize=(11, 10))
    x_labels = df['GPU'] + '\n(' + df['Year'].astype(str) + ')'

    line1 = ax1.plot(x_labels, df['Raw_Power'], marker='^', color='#00ffcc', linewidth=3, markersize=8, label='Raw Hardware Power (PassMark)')
    line2 = ax1.plot(x_labels, df['Average_Demand'], marker='x', color='#ff3333', linewidth=2, linestyle='--', label='Avg. Recommended Requirements (Top AAA)')
    line3 = ax1.plot(x_labels, df['Adjusted_Power'], marker='o', color='#ffaa00', linewidth=4, markersize=9, label='Demand-Adjusted Performance')

    ax1.fill_between(x_labels, df['Adjusted_Power'], df['Raw_Power'], color='#00ffcc', alpha=0.1)

    ax1.set_ylabel('Score (PassMark G3D Mark)', fontweight='bold', fontsize=11, color='#eeeeee')
    ax1.tick_params(axis='y', labelcolor='#eeeeee')
    ax1.set_xlabel('GPU Generation', fontweight='bold', fontsize=11)
    ax1.grid(True, linestyle=':', alpha=0.3)
    ax1.set_title(f'Performance vs. Game Engine Demand (Series {series})', fontsize=13, fontweight='bold', pad=15)
    
    lines_ax1 = line1 + line2 + line3
    labels_ax1 = [l.get_label() for l in lines_ax1]
    ax1.legend(lines_ax1, labels_ax1, loc='upper left', facecolor='#1a1a1a', edgecolor='none')

    money_color = '#2ecc71'
    line4 = ax2.plot(x_labels, df['Adjusted_Price'], marker='D', color=money_color, linestyle='-.', linewidth=2.5, markersize=8, label='Inflation-Adjusted Launch Price (US$)')
    
    ax2.set_ylabel('Adjusted Price (Dollars)', fontweight='bold', fontsize=11, color=money_color)
    ax2.tick_params(axis='y', labelcolor=money_color)
    ax2.grid(True, linestyle=':', alpha=0.3)

    ax3 = ax2.twinx()
    ratio_color = '#bd93f9'
    line5 = ax3.plot(x_labels, df['Performance_Per_Dollar'], marker='s', color=ratio_color, linestyle=':', linewidth=2.5, markersize=8, label='Performance per Dollar (Score/US$)')
    
    ax3.set_ylabel('Performance per Dollar (Score/US$)', fontweight='bold', fontsize=11, color=ratio_color)
    ax3.tick_params(axis='y', labelcolor=ratio_color)

    ax2.set_xlabel('GPU Generation', fontweight='bold', fontsize=11)

    lines_ax2 = line4 + line5
    labels_ax2 = [l.get_label() for l in lines_ax2]
    ax2.legend(lines_ax2, labels_ax2, loc='upper left', facecolor='#1a1a1a', edgecolor='none')

    fig.suptitle('Performance Inflation Dashboard', fontsize=16, fontweight='bold', y=0.98)
    fig.tight_layout()
    plt.subplots_adjust(top=0.92, hspace=0.3)
    
    plt.show()

def generate_extended_charts(df, series):
    x_labels_nv = df['GPU'] + '\n(' + df['Year'].astype(str) + ')'
    
    fig1, ax1 = plt.subplots(figsize=(12, 7))
    
    ax1.plot(x_labels_nv, df['Raw_Power'], marker='^', color='#00ffcc', linewidth=3, markersize=8, label='Raw Hardware Power (PassMark)')
    ax1.plot(x_labels_nv, df['Average_Demand'], marker='x', color='#ffffff', linewidth=2, linestyle='--', alpha=0.7, label='Avg. Recommended Requirements (Top AAA)')
    ax1.plot(x_labels_nv, df['Adjusted_Power'], marker='o', color='#ffaa00', linewidth=3, markersize=8, label='Demand-Adjusted Performance')
    
    ax1.fill_between(x_labels_nv, df['Adjusted_Power'], df['Raw_Power'], color='#00ffcc', alpha=0.1)

    ax1.set_ylabel('Score (PassMark G3D Mark)', fontweight='bold')
    ax1.set_title(f'NVIDIA Performance vs. Game Engine Demand (Series {series})', fontsize=14, fontweight='bold', pad=15)
    ax1.grid(True, linestyle=':', alpha=0.3)
    ax1.legend(loc='upper left', facecolor='#1a1a1a', edgecolor='none')
    fig1.tight_layout()

    x_labels_comp = df.apply(
        lambda row: f"{row['GPU']} vs {row['AMD_GPU']}\n({row['Year']})" 
        if pd.notna(row.get('AMD_GPU')) and row.get('AMD_GPU') 
        else f"{row['GPU']}\n({row['Year']})", 
        axis=1
    )

    fig2, (ax2, ax3) = plt.subplots(nrows=2, ncols=1, figsize=(14, 10))
    
    money_color_nv = '#2ecc71'
    money_color_amd = '#1b9e77'
    
    ax2.plot(x_labels_comp, df['Adjusted_Price'], marker='D', color=money_color_nv, linestyle='-', linewidth=2.5, markersize=8, label='NVIDIA Inflation-Adjusted Launch Price (US$)')
    if 'AMD_Adjusted_Price' in df.columns:
        ax2.plot(x_labels_comp, df['AMD_Adjusted_Price'], marker='D', color=money_color_amd, linestyle='--', linewidth=2.5, markersize=8, label='AMD Inflation-Adjusted Launch Price (US$)')
    
    ax2.set_ylabel('Adjusted Price (US$)', fontweight='bold')
    ax2.set_title('Inflation-Adjusted Launch Price Comparison', fontsize=14, fontweight='bold', pad=10)
    ax2.grid(True, linestyle=':', alpha=0.3)
    ax2.legend(loc='center left', bbox_to_anchor=(1.02, 0.5), facecolor='#1a1a1a', edgecolor='none')

    ratio_color_nv = '#bd93f9'
    ratio_color_amd = '#ff79c6'
    
    ax3.plot(x_labels_comp, df['Performance_Per_Dollar'], marker='s', color=ratio_color_nv, linestyle='-', linewidth=2.5, markersize=8, label='NVIDIA Performance per Dollar (Score/US$)')
    if 'AMD_Perf_Per_Dollar' in df.columns:
        ax3.plot(x_labels_comp, df['AMD_Perf_Per_Dollar'], marker='s', color=ratio_color_amd, linestyle='--', linewidth=2.5, markersize=8, label='AMD Performance per Dollar (Score/US$)')
    
    ax3.set_ylabel('Performance per Dollar (Score/US$)', fontweight='bold')
    ax3.set_title('Cost-Benefit Over Time', fontsize=14, fontweight='bold', pad=10)
    ax3.set_xlabel('GPU Generation', fontweight='bold', fontsize=12)
    ax3.grid(True, linestyle=':', alpha=0.3)
    ax3.legend(loc='center left', bbox_to_anchor=(1.02, 0.5), facecolor='#1a1a1a', edgecolor='none')

    fig2.suptitle('Competitor Analysis: Market Price & Cost-Benefit', fontsize=16, fontweight='bold', y=0.98)
    fig2.tight_layout(rect=[0, 0, 0.82, 0.95], h_pad=2.0)
    
    plt.show()

if __name__ == "__main__":
    run_pipeline()