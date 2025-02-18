# NASA API Key Required
# Visit https://api.nasa.gov/ to get your own API key and replace "YOUR_NASA_API_KEY_HERE"
import requests
import json
import datetime
import os

# NASA API Endpoints
NASA_SOLAR_FLARE_API = "https://api.nasa.gov/DONKI/FLR"
NASA_GEO_STORM_API = "https://api.nasa.gov/DONKI/GST"
NASA_CME_API = "https://api.nasa.gov/DONKI/CME"
NASA_SEP_API = "https://api.nasa.gov/DONKI/SEP"
NASA_IPS_API = "https://api.nasa.gov/DONKI/IPS"

# Your NASA API Key
API_KEY = "YOUR_NASA_API_KEY_HERE"  # Get your key from https://api.nasa.gov/

DATA_FILE = "data/space_weather_data.json"

# Function to process solar flare data
def process_solar_flare_data(flares_data):
    """Processes solar flare data, estimating duration if not provided."""
    processed_flares = []
    from datetime import datetime

    fmt = "%Y-%m-%dT%H:%MZ"
    
    for flare in flares_data:
        begin_time = flare.get("beginTime", "Unknown")
        peak_time = flare.get("peakTime", "Unknown")
        end_time = flare.get("endTime", None)  # Sometimes missing
        duration_seconds = "N/A"
        
        try:
            if begin_time != "Unknown":
                begin_dt = datetime.strptime(begin_time, fmt)
                
                if end_time:
                    end_dt = datetime.strptime(end_time, fmt)
                    duration_seconds = (end_dt - begin_dt).total_seconds()
                elif peak_time != "Unknown":
                    peak_dt = datetime.strptime(peak_time, fmt)
                    duration_seconds = (peak_dt - begin_dt).total_seconds()
                
                duration_seconds = max(duration_seconds, 1) if isinstance(duration_seconds, (int, float)) else "N/A"
        
        except ValueError:
            duration_seconds = "N/A"

        processed_flares.append({
            "classType": flare.get("classType", "Unknown"),
            "beginTime": begin_time,
            "peakTime": peak_time,
            "endTime": end_time,
            "duration": duration_seconds
        })
    
    return processed_flares

# Function to fetch NASA space weather data
def fetch_space_weather():
    try:
        end_date = datetime.datetime.utcnow().strftime("%Y-%m-%d")
        start_date = (datetime.datetime.utcnow() - datetime.timedelta(days=10*365)).strftime("%Y-%m-%d")

        params = {
            "startDate": start_date,
            "endDate": end_date,
            "api_key": API_KEY
        }

        # Fetch NASA Solar Flare Data
        print("Fetching Solar Flares...")
        flares_response = requests.get(NASA_SOLAR_FLARE_API, params=params)
        flares_data = flares_response.json() if flares_response.status_code == 200 else []

        print(f"Found {len(flares_data)} solar flares")

        # Process solar flare data (estimate durations)
        processed_flares = process_solar_flare_data(flares_data)

        # Fetch NASA Geomagnetic Storm Data
        print("Fetching Geomagnetic Storms...")
        geo_storm_response = requests.get(NASA_GEO_STORM_API, params=params)
        geo_storm_data = geo_storm_response.json() if geo_storm_response.status_code == 200 else []
        print(f"Found {len(geo_storm_data)} geomagnetic storms")

        # Fetch CME Data
        print("Fetching Coronal Mass Ejections (CME)...")
        cme_response = requests.get(NASA_CME_API, params=params)
        cme_data = cme_response.json() if cme_response.status_code == 200 else []
        print(f"Found {len(cme_data)} CMEs")

        # Fetch SEP Data
        print("Fetching Solar Energetic Particles (SEP)...")
        sep_response = requests.get(NASA_SEP_API, params=params)
        sep_data = sep_response.json() if sep_response.status_code == 200 else []
        print(f"Found {len(sep_data)} SEP events")

        # Fetch IPS Data
        print("Fetching Interplanetary Shocks (IPS)...")
        ips_response = requests.get(NASA_IPS_API, params=params)
        ips_data = ips_response.json() if ips_response.status_code == 200 else []
        print(f"Found {len(ips_data)} IPS events")

        save_data_to_file(processed_flares, geo_storm_data, cme_data, sep_data, ips_data)

    except Exception as e:
        print(f"Error fetching space weather data: {e}")

# Function to save fetched data
def save_data_to_file(flares_data, geo_storm_data, cme_data, sep_data, ips_data):
    try:
        formatted_storms = []
        for storm in geo_storm_data:
            start_time = storm.get("startTime", "Unknown")
            kp_values = storm.get("allKpIndex", [])
            kp_index = kp_values[0].get("kpIndex", "N/A") if kp_values else "N/A"
            
            formatted_storms.append({
                "startTime": start_time,
                "kpIndex": kp_index
            })

        # Format CME Data (Prevent 'NoneType' errors)
        formatted_cmes = []
        for cme in cme_data:
            cme_analysis = cme.get("cmeAnalyses", [{}])
            formatted_cmes.append({
                "startTime": cme.get("startTime", "Unknown"),
                "speed": cme_analysis[0].get("speed", "N/A") if cme_analysis else "N/A",
                "type": cme_analysis[0].get("type", "N/A") if cme_analysis else "N/A"
            })

        # Format SEP Data (Prevent 'NoneType' errors)
        formatted_seps = []
        for sep in sep_data:
            sep_instruments = sep.get("instruments", [{}])
            formatted_seps.append({
                "eventTime": sep.get("eventTime", "Unknown"),
                "source": sep_instruments[0].get("displayName", "N/A") if sep_instruments else "N/A"
            })

        # Format IPS Data (Prevent 'NoneType' errors)
        formatted_ips = []
        for ips in ips_data:
            formatted_ips.append({
                "eventTime": ips.get("eventTime", "Unknown"),
                "location": ips.get("location", "Unknown")
            })

        # Save data to JSON
        data = {
            "timestamp": str(datetime.datetime.now()),
            "solar_flares": flares_data,
            "geomagnetic_storms": formatted_storms,
            "coronal_mass_ejections": formatted_cmes,
            "solar_energetic_particles": formatted_seps,
            "interplanetary_shocks": formatted_ips
        }

        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=4)

        print("Data saved successfully.")

    except Exception as e:
        print(f"Error saving data: {e}")

# Run function when script executes
if __name__ == "__main__":
    fetch_space_weather()
