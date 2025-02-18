🚀 AI Space Weather App

Overview

The AI Space Weather Monitor is an application that fetches and processes real-time space weather data from NASA's DONKI API. It predicts upcoming solar events using machine learning and presents relevant information about solar flares, geomagnetic storms, coronal mass ejections (CME), solar energetic particles (SEP), and interplanetary shocks (IPS). The GUI (built with Tkinter) displays an animated prediction screen alongside a history of past events and predictions.

Features:

Real-time Data Fetching: Retrieves data on solar flares, geomagnetic storms, CME, SEP, and IPS events.

Machine Learning Predictions (Random Forest): Uses a trained model to predict future solar flares.
- The intensity class of the next solar flare (e.g., X-Class, M-Class, C-Class)
- The time interval until the next event (in days)

Historical Data Analysis: Stores past predictions and provides insights based on previous observations.

Graphical User Interface: Displays space weather events and AI predictions in an interactive UI.

Automated Updates: Runs periodic updates to ensure the latest space weather data is available.

🎯Accuracy
The AI model is trained on 10 years of data from NASA. The model extracts nine essential features from each event—capturing the day, hour, month, intensity, storm level, duration, and counts of CME, SEP, and IPS and then enriches this data by adding weekday and lag to create a robust 10-dimensional feature vector.

Model Accuracy
- Event Classification: 78%
- Time Prediction Error: 1.67 days

In ai_space_weather/weather_fetch.py, replace the placeholder API key with your valid NASA API key:

Install all requirements
pip install -r requirements.txt

If running on Windows
example: cd /d D:/AI-Space-Weather-App (Choose your installation path)
python -m ai_space_weather.main

Running the App from Executable
The .exe file, you can run it from the dist/ folder:
dist/main.exe

If running on Linux or Mac
cd /path/to/AI-Space-Weather-App
python3 -m ai_space_weather.main

Or open by running in scripts bat(Windows) or sh(Linux/Mac)

☁️Update weather information
python -m ai_space_weather.weather_fetch
This will update the data/space_weather_data.json file with the latest information.

🧠 Retraining the AI Model
To retrain the AI model using the updated dataset:
python -c "from ai_space_weather.ai_model import train_ai_model; train_ai_model()"
This will retrain the AI model and save it for future predictions.

🏗️ Updating the Executable
To generate an executable version of the application, use:
pyinstaller --onefile --windowed --add-data "data;data" ai_space_weather/main.py
The executable will be created inside the dist/ directory.

Video Demo of the UI
https://youtu.be/lBa6XBLS1_Y
