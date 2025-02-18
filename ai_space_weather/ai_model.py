import numpy as np
import json
import os
import pickle
import sys
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, mean_absolute_error
from datetime import datetime, timedelta

# Resource path helper: works for development and for PyInstaller exe.
def resource_path(relative_path):
    """Get absolute path to resource, works for dev and PyInstaller."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

MODEL_FILE = "data/solar_flare_model.pkl"
TIME_MODEL_FILE = "data/solar_flare_time_model.pkl"
DATA_FILE = "data/space_weather_data.json"
PREDICTION_FILE = "data/solar_predictions.json"

def extract_features(entry, geo_storm_data, cme_data, sep_data, ips_data):
    """
    Extract base features from a solar flare entry.
    Returns a list:
    [day, hour, month, intensity, storm_level, duration, cme_count, sep_count, ips_count]
    """
    time_str = entry.get("beginTime", "2024-01-01T00:00Z")
    try:
        flare_datetime = datetime.strptime(time_str, "%Y-%m-%dT%H:%MZ")
    except ValueError:
        flare_datetime = datetime(2024, 1, 1)
    day = flare_datetime.day
    hour = flare_datetime.hour
    month = flare_datetime.month

    flare_class_map = {"X": 5, "M": 4, "C": 3, "B": 2, "A": 1}
    class_letter = entry.get("classType", "M1")[0]
    intensity = flare_class_map.get(class_letter, 1)

    # Use the flare's date (YYYY-MM-DD) to match events on the same day.
    date_prefix = time_str[:10]
    nearest_storm = next((storm for storm in geo_storm_data if storm.get("startTime", "").startswith(date_prefix)), None)
    storm_level = float(nearest_storm.get("kpIndex", 0)) if nearest_storm else 0

    duration = entry.get("duration", 0)
    if not isinstance(duration, (int, float)):
        duration = 0

    flare_date = flare_datetime.strftime("%Y-%m-%d")
    cme_count = sum(1 for cme in cme_data if cme.get("startTime", "").startswith(flare_date))
    sep_count = sum(1 for sep in sep_data if sep.get("eventTime", "").startswith(flare_date))
    ips_count = sum(1 for ips in ips_data if ips.get("eventTime", "").startswith(flare_date))

    return [day, hour, month, intensity, storm_level, duration, cme_count, sep_count, ips_count]

def train_ai_model():
    if not os.path.exists(resource_path(DATA_FILE)):
        print("No data available for training.")
        return

    with open(resource_path(DATA_FILE), "r") as f:
        data = json.load(f)

    solar_flare_data = data.get("solar_flares", [])
    geo_storm_data = data.get("geomagnetic_storms", [])
    cme_data = data.get("coronal_mass_ejections", [])
    sep_data = data.get("solar_energetic_particles", [])
    ips_data = data.get("interplanetary_shocks", [])

    if len(solar_flare_data) < 10:
        print("Not enough data for training.")
        return

    # Sort flare data chronologically
    solar_flare_data.sort(key=lambda x: x.get("beginTime", ""))

    features = []       # Final features for training
    class_labels = []   # Target intensity (for classification)
    reg_targets = []    # Target: time interval (in days) from current event to next event

    # Use events where both a previous and a next event exist (i=1 to len-2)
    for i in range(1, len(solar_flare_data) - 1):
        current_entry = solar_flare_data[i]
        prev_entry = solar_flare_data[i - 1]
        next_entry = solar_flare_data[i + 1]

        # Extract base features for current event.
        feat = extract_features(current_entry, geo_storm_data, cme_data, sep_data, ips_data)
        # feat: [day, hour, month, intensity, storm_level, duration, cme_count, sep_count, ips_count]

        # Compute additional temporal features.
        time_str = current_entry.get("beginTime", "2024-01-01T00:00Z")
        try:
            current_dt = datetime.strptime(time_str, "%Y-%m-%dT%H:%MZ")
        except ValueError:
            current_dt = datetime(2024, 1, 1)
        weekday = current_dt.weekday()  # 0=Monday, ... 6=Sunday

        # Compute lag: difference in days between current event and previous event.
        time_str_prev = prev_entry.get("beginTime", "2024-01-01T00:00Z")
        try:
            prev_dt = datetime.strptime(time_str_prev, "%Y-%m-%dT%H:%MZ")
        except ValueError:
            prev_dt = datetime(2024, 1, 1)
        lag = max((current_dt - prev_dt).days, 1)

        # Build full feature vector for classification:
        # [day, hour, month, weekday, storm_level, duration, lag, cme_count, sep_count, ips_count]
        full_features = [feat[0], feat[1], feat[2], weekday, feat[4], feat[5], lag, feat[6], feat[7], feat[8]]
        features.append(full_features)

        # Classification target: intensity (feat[3])
        class_labels.append(feat[3])

        # Regression target: time interval between current event and next event.
        time_str_next = next_entry.get("beginTime", "2024-01-01T00:00Z")
        try:
            next_dt = datetime.strptime(time_str_next, "%Y-%m-%dT%H:%MZ")
        except ValueError:
            next_dt = datetime(2024, 1, 1)
        interval = max((next_dt - current_dt).days, 1)
        reg_targets.append(interval)

    # Build separate feature arrays:
    # For classifier, use the full feature vector.
    X_class = np.array(features)
    # For regressor, remove the lag feature (element at index 6).
    X_reg = np.array([feat[:6] + feat[7:] for feat in features])
    y_class = np.array(class_labels, dtype=int)
    y_time = np.array(reg_targets, dtype=int)

    # Split into training and testing sets
    X_train_class, X_test_class, X_train_reg, X_test_reg, y_train_class, y_test_class, y_train_time, y_test_time = train_test_split(
        X_class, X_reg, y_class, y_time, test_size=0.2, random_state=42
    )

    # Train classifier (predict flare intensity)
    classifier = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
    classifier.fit(X_train_class, y_train_class)
    y_pred = classifier.predict(X_test_class)
    acc = accuracy_score(y_test_class, y_pred)
    print("Model Accuracy:", acc)
    with open(resource_path(MODEL_FILE), "wb") as f:
        pickle.dump(classifier, f)

    # Train regressor (predict time interval until next flare) using features without lag
    regressor = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)
    regressor.fit(X_train_reg, y_train_time)
    y_time_pred = regressor.predict(X_test_reg)
    mae = mean_absolute_error(y_test_time, y_time_pred)
    print("Time Prediction Error:", mae)
    with open(resource_path(TIME_MODEL_FILE), "wb") as f:
        pickle.dump(regressor, f)

def load_or_train_models(retrain=False):
    model_path = resource_path(MODEL_FILE)
    time_model_path = resource_path(TIME_MODEL_FILE)
    if retrain or not (os.path.exists(model_path) and os.path.exists(time_model_path)):
        print("Training models...")
        train_ai_model()
    with open(model_path, "rb") as f:
        classifier = pickle.load(f)
    with open(time_model_path, "rb") as f:
        regressor = pickle.load(f)
    return classifier, regressor

def save_prediction(predicted_class, estimated_days):
    estimated_date = (datetime.utcnow() + timedelta(days=estimated_days)).strftime("%Y-%m-%d")
    prediction_entry = {
        "predicted_class": predicted_class,
        "estimated_days": estimated_days,
        "estimated_date": estimated_date,
        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    }
    if os.path.exists(resource_path(PREDICTION_FILE)):
        with open(resource_path(PREDICTION_FILE), "r") as f:
            predictions = json.load(f)
    else:
        predictions = []
    for existing in predictions:
        if existing["predicted_class"] == predicted_class and existing["estimated_date"] == estimated_date:
            print("Duplicate prediction detected, not saving.")
            return
    predictions.append(prediction_entry)
    with open(resource_path(PREDICTION_FILE), "w") as f:
        json.dump(predictions, f, indent=4)
    print("Prediction saved successfully.")

def predict_next_solar_event():
    if not (os.path.exists(resource_path(DATA_FILE)) and os.path.exists(resource_path(MODEL_FILE)) and os.path.exists(resource_path(TIME_MODEL_FILE))):
        return "No prediction available (Train model first)"
    with open(resource_path(DATA_FILE), "r") as f:
        data = json.load(f)
    solar_flares = data.get("solar_flares", [])
    geo_storm_data = data.get("geomagnetic_storms", [])
    cme_data = data.get("coronal_mass_ejections", [])
    sep_data = data.get("solar_energetic_particles", [])
    ips_data = data.get("interplanetary_shocks", [])
    if len(solar_flares) < 2:
        return "Not enough data for prediction"

    # For prediction, use the latest flare and compute lag using the previous flare.
    latest_flare = solar_flares[-1]
    prev_flare = solar_flares[-2]
    feat = extract_features(latest_flare, geo_storm_data, cme_data, sep_data, ips_data)
    try:
        current_dt = datetime.strptime(latest_flare.get("beginTime", "2024-01-01T00:00Z"), "%Y-%m-%dT%H:%MZ")
    except ValueError:
        current_dt = datetime(2024, 1, 1)
    try:
        prev_dt = datetime.strptime(prev_flare.get("beginTime", "2024-01-01T00:00Z"), "%Y-%m-%dT%H:%MZ")
    except ValueError:
        prev_dt = datetime(2024, 1, 1)
    weekday = current_dt.weekday()
    lag = max((current_dt - prev_dt).days, 1)
    # Build feature vector for classification (with lag)
    full_feat = [feat[0], feat[1], feat[2], weekday, feat[4], feat[5], lag, feat[6], feat[7], feat[8]]
    # For regression, remove lag (element at index 6)
    reg_feat = full_feat[:6] + full_feat[7:]
    classifier, regressor = load_or_train_models(retrain=False)
    test_features_class = np.array([full_feat])
    test_features_reg = np.array([reg_feat])
    class_prediction = classifier.predict(test_features_class)[0]
    time_prediction = regressor.predict(test_features_reg)[0]
    time_prediction = max(time_prediction, 1)
    prediction_map = {5: "X-Class", 4: "M-Class", 3: "C-Class", 2: "B-Class", 1: "A-Class"}
    predicted_class = prediction_map.get(class_prediction, f"Unknown ({class_prediction})")
    try:
        latest_dt = datetime.strptime(latest_flare.get("beginTime", "2024-01-01T00:00Z"), "%Y-%m-%dT%H:%MZ")
    except ValueError:
        latest_dt = datetime(2024, 1, 1)
    estimated_next_event = latest_dt + timedelta(days=time_prediction)
    today = datetime.utcnow()
    estimated_days = (estimated_next_event - today).days
    estimated_days = max(estimated_days, 1)
    save_prediction(predicted_class, estimated_days)
    return f"Predicted Solar Event Class: {predicted_class} (Estimated in {estimated_days} days)"

def load_past_predictions():
    if os.path.exists(resource_path(PREDICTION_FILE)):
        with open(resource_path(PREDICTION_FILE), "r") as f:
            predictions = json.load(f)
        if predictions:
            formatted_predictions = []
            for p in predictions:
                try:
                    ts = datetime.strptime(p['timestamp'], "%Y-%m-%dT%H:%M:%SZ")
                    ts_formatted = ts.strftime("%b %d, %Y %I:%M:%S %p")
                except Exception:
                    ts_formatted = p['timestamp']
                formatted_predictions.append(f"{ts_formatted}: {p['predicted_class']} (in {p['estimated_days']} days)")
            return "\n".join(formatted_predictions)
        else:
            return "No past predictions available."
    else:
        return "No past predictions available."

if __name__ == "__main__":
    # Uncomment the following line to train the models before prediction
    # train_ai_model()
    print(predict_next_solar_event())
