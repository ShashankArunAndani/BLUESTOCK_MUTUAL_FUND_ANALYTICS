import requests
import pandas as pd
from pathlib import Path

# --------------------------------------------------
# Configuration
# --------------------------------------------------

BASE_URL = "https://api.mfapi.in/mf"

RAW_FOLDER = Path("data/raw")
RAW_FOLDER.mkdir(parents=True, exist_ok=True)

SCHEMES = {
    "HDFC_Top_100_Direct": 125497,
    "SBI_Bluechip": 119551,
    "ICICI_Bluechip": 120503,
    "Nippon_Large_Cap": 118632,
    "Axis_Bluechip": 119092,
    "Kotak_Bluechip": 120841
}

# --------------------------------------------------
# Function to Fetch NAV Data
# --------------------------------------------------

def fetch_nav(scheme_name, scheme_code):
    url = f"{BASE_URL}/{scheme_code}"

    print("=" * 80)
    print(f"Fetching: {scheme_name}")
    print(f"Scheme Code : {scheme_code}")
    print(f"URL         : {url}")

    try:
        response = requests.get(url, timeout=20)

        response.raise_for_status()

        json_data = response.json()

        if "data" not in json_data:
            print("No NAV data found.")
            return

        df = pd.DataFrame(json_data["data"])

        # Save CSV
        output_file = RAW_FOLDER / f"{scheme_name}.csv"
        df.to_csv(output_file, index=False)

        print(f"Records Retrieved : {len(df)}")
        print(f"Saved To          : {output_file}")

        # Optional: Print Meta Information
        """
        print("\nFund Information")
        print("-" * 40)

        meta = json_data.get("meta", {})

        for key, value in meta.items():
            print(f"{key:20}: {value}")

        print("-" * 40)
        """

    except requests.exceptions.RequestException as e:
        print(f"Request Error : {e}")

    except Exception as e:
        print(f"Unexpected Error : {e}")

# --------------------------------------------------
# Main
# --------------------------------------------------

def main():

    print("\n")
    print("#" * 100)
    print("BLUESTOCK MUTUAL FUND ANALYTICS")
    print("LIVE NAV DATA FETCH")
    print("#" * 100)

    for scheme_name, scheme_code in SCHEMES.items():
        fetch_nav(scheme_name, scheme_code)

    print("\n")
    print("=" * 100)
    print("All NAV files downloaded successfully.")
    print("=" * 100)

if __name__ == "__main__":
    main()