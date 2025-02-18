🚀 AI Space Weather App

Overview

The AI Space Weather Monitor is an application that fetches and processes real-time space weather data from NASA's DONKI API. It predicts upcoming solar events using machine learning and presents relevant information about solar flares, geomagnetic storms, coronal mass ejections (CME), solar energetic particles (SEP), and interplanetary shocks (IPS).

Features:

Real-time Data Fetching: Retrieves data on solar flares, geomagnetic storms, CME, SEP, and IPS events.

Machine Learning Predictions: Uses a trained model to predict future solar flares.

Historical Data Analysis: Stores past predictions and provides insights based on previous observations.

Graphical User Interface: Displays space weather events and AI predictions in an interactive UI.

Automated Updates: Runs periodic updates to ensure the latest space weather data is available.

📂 Project Structure
bash
Copy
Edit
AI-Space-Weather-App/
│── ai_space_weather/
│   │── __init__.py
│   │── ai_model.py
│   │── main.py
│   │── weather_fetch.py
│
│── data/                  # Stores fetched space weather data
│── dist/                  # Contains the built executable file
│── logs/                  # Logs for debugging
│── scripts/               # Scripts for launching the application
│   │── launch_app.bat
│   │── launch_app.sh
│
│── requirements.txt       # Python dependencies
│── README.md              # This file
│── main.spec              # PyInstaller spec file
│── SpaceWeatherApp.spec   # PyInstaller spec file

📦 Installation
1️⃣ Clone the Repository
git clone https://github.com/your-username/AI-Space-Weather-App.git
cd AI-Space-Weather-App
2️⃣ Install Dependencies
Ensure you have Python 3.x installed. Then, install the required dependencies:

pip install -r requirements.txt
▶️ Running the Application
1️⃣ Running the App using Python

If you have Python installed, navigate to the project directory and run:
sample format: cd /d D:\AI-Space-Weather-App  # For Windows users
python -m ai_space_weather.main
or, on Linux/macOS:

cd /d D:/AI-Space-Weather-App  # If running on Windows in cmd
python -m ai_space_weather.main
2️⃣ Running the App from Executable
The .exe file, you can run it from the dist/ folder:
dist/main.exe

Alternatively, use the batch script:

scripts/launch_app.bat
or for Linux/macOS:

sh scripts/launch_app.sh
🔄 Updating Space Weather Data
To fetch up-to-date NASA space weather data, run:

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

