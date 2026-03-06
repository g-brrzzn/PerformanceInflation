RAWG_API_KEY = "YOUR_API_KEY_HERE"
GAMES_LIMIT_PER_YEAR = 5
CHOSEN_SERIES = '60'

def generate_gpu_list(desired_series):
    return [
        f"GTX 9{desired_series}", f"GTX 10{desired_series}", f"RTX 20{desired_series}",
        f"RTX 30{desired_series}", f"RTX 40{desired_series}", f"RTX 50{desired_series}"
    ]