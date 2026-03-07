RAWG_API_KEY = "YOUR_API_KEY_HERE"
GAMES_LIMIT_PER_YEAR = 5
CHOSEN_SERIES = '60'
START_GENERATION_INDEX = 2

def generate_gpu_list(desired_series):
    gpus = [
        f"GTX 6{desired_series}",
        f"GTX 7{desired_series}",
        f"GTX 9{desired_series}",
        f"GTX 10{desired_series}",
        f"RTX 20{desired_series}",
        f"RTX 30{desired_series}",
        f"RTX 40{desired_series}",
        f"RTX 50{desired_series}"
    ]
    return gpus[START_GENERATION_INDEX:]

def generate_competitor_list(desired_series):
    tier_mapping = {
        '50': ('HD 7770', 'R7 260X', 'R7 370', 'RX 460', '500'),
        '60': ('HD 7850', 'R9 270X', 'R9 380', 'RX 480', '600'),
        '70': ('HD 7950', 'R9 280X', 'R9 390', 'RX Vega 56', '700 XT'),
        '80': ('HD 7970', 'R9 290X', 'R9 Fury', 'RX Vega 64', '800 XT'),
        '90': ('HD 7990', 'R9 295X2', 'R9 Fury X', 'Radeon VII', '900 XTX')
    }
    
    if desired_series not in tier_mapping:
        return []
        
    gen_2012, gen_2013, gen_2015, gen_2016, modern_suffix = tier_mapping[desired_series]
    rx5000_suffix = f"{modern_suffix} XT" if desired_series == '60' else modern_suffix
    
    amd_gpus = [
        gen_2012,
        gen_2013,
        gen_2015,
        gen_2016,
        f"RX 5{rx5000_suffix}",
        f"RX 6{modern_suffix}",
        f"RX 7{modern_suffix}",
        f"RX 8{modern_suffix}"
    ]
    return amd_gpus[START_GENERATION_INDEX:]