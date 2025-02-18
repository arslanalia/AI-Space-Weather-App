import tkinter as tk
import os
import json
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
import random, math, time, threading
from datetime import datetime
from ai_space_weather.ai_model import predict_next_solar_event, load_past_predictions
from ai_space_weather.weather_fetch import fetch_space_weather
from PIL import Image, ImageTk  # Only if you plan to use images for Earth, etc.
# Trigger language analysis
# ---------------------------------------
# Dynamic Starfield for the Prediction Tab
# ---------------------------------------
def create_starfield(canvas, width, height, num_stars=150):
    """Draw random stars on the canvas and start the twinkling effect."""
    canvas.delete("star")
    for _ in range(num_stars):
        x = random.randint(0, width)
        y = random.randint(0, height)
        size = random.randint(1, 3)
        canvas.create_oval(x, y, x + size, y + size, fill="white", outline="", tag="star")
    twinkle_stars(canvas)

def twinkle_stars(canvas):
    """Randomly adjust star colors to simulate twinkling."""
    star_items = canvas.find_withtag("star")
    for star in star_items:
        # Increase chance to twinkle to 30%
        if random.random() < 0.3:
            # Choose colors that differ noticeably from white
            new_color = random.choice(["white", "lightyellow", "gold", "whitesmoke"])
            canvas.itemconfig(star, fill=new_color)
    # Update every 200ms (adjust as desired)
    canvas.after(200, lambda: twinkle_stars(canvas))
    
def start_prediction_animation(canvas):
    # Wait until the canvas has a valid size
    width = int(canvas.winfo_width())
    height = int(canvas.winfo_height())
    if width < 50 or height < 50:
        canvas.after(100, lambda: start_prediction_animation(canvas))
        return

    # Save the current size for later comparison
    canvas.last_size = (width, height)

    # Initial starfield
    create_starfield(canvas, width, height)

    # Center the Sun using the current canvas size
    sun_center_x = width // 2
    sun_center_y = height // 2
    sun_radius = 30

    # Draw the glowing background for the Sun
    canvas.create_oval(
        sun_center_x - sun_radius*2, sun_center_y - sun_radius*2,
        sun_center_x + sun_radius*2, sun_center_y + sun_radius*2,
        fill="yellow", outline="", stipple="gray50", tag="sun"
    )
    # Draw the Sun itself
    canvas.create_oval(
        sun_center_x - sun_radius, sun_center_y - sun_radius,
        sun_center_x + sun_radius, sun_center_y + sun_radius,
        fill="yellow", outline="", tag="sun"
    )

    # Earth orbit parameters
    earth_radius = 10
    orbit_radius = 100
    angle = 0
    # Draw Earth and tag it for easy management
    earth_item = canvas.create_oval(
        sun_center_x + orbit_radius - earth_radius,
        sun_center_y - earth_radius,
        sun_center_x + orbit_radius + earth_radius,
        sun_center_y + earth_radius,
        fill="blue", outline="", tag="earth"
    )

    def animate_orbit():
        nonlocal angle
        rad = math.radians(angle)
        ex = sun_center_x + orbit_radius * math.cos(rad)
        ey = sun_center_y + orbit_radius * math.sin(rad)
        canvas.coords("earth", ex - earth_radius, ey - earth_radius, ex + earth_radius, ey + earth_radius)
        # Optional: add a short trail dot
        trail = canvas.create_oval(ex-2, ey-2, ex+2, ey+2, fill="lightblue", outline="", tag="trail")
        canvas.after(500, lambda: canvas.delete(trail))
        angle = (angle + 2) % 360
        canvas.after(50, animate_orbit)

    animate_orbit()

    def update_prediction_text():
        event_str = predict_next_solar_event()
        canvas.itemconfig("pred_text", text=event_str)
        canvas.after(30000, update_prediction_text)

    update_prediction_text()

    # Bind a resize event to reinitialize the entire animation if the canvas size changes
    def handle_resize(event):
        new_width, new_height = event.width, event.height
        # Check if size actually changed from last time
        if not hasattr(canvas, "last_size") or (new_width, new_height) != canvas.last_size:
            canvas.last_size = (new_width, new_height)
            canvas.delete("all")  # Clear all items
            start_prediction_animation(canvas)
    canvas.bind("<Configure>", handle_resize)

    # Create the prediction text near the bottom center
    prediction_text_id = canvas.create_text(
        width // 2, height - 30,
        text="Next Predicted Event: ...",
        fill="cyan",
        font=("Helvetica", 20, "bold"),
        anchor="center"
    )

    def update_prediction_text():
        event_str = predict_next_solar_event()
        canvas.itemconfig(prediction_text_id, text=event_str)
        canvas.after(30000, update_prediction_text)

    update_prediction_text()

    def handle_resize(event):
        new_width, new_height = event.width, event.height
        # Redraw starfield
        create_starfield(canvas, new_width, new_height)
        # The Sun/Earth remain at their initial positions unless you recalculate them here.
        # Re-center the prediction text at bottom center:
        canvas.coords(prediction_text_id, new_width // 2, new_height - 30)

    canvas.bind("<Configure>", handle_resize)


# ---------------------------------------
# History Tab Functions
# ---------------------------------------
import os
import json
import time
import threading
from datetime import datetime
import tkinter as tk

def format_datetime(dt_str):
    """
    Attempt to parse a date/time string and return a formatted version.
    Tries two common formats; adjust as needed.
    """
    try:
        # Try ISO format: "YYYY-MM-DDT%H:%MZ"
        dt = datetime.strptime(dt_str, "%Y-%m-%dT%H:%MZ")
        return dt.strftime("%b %d, %Y %I:%M %p")
    except Exception:
        pass
    try:
        # Try "YYYY-MM-DD HH:MM:SS.microseconds"
        dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S.%f")
        return dt.strftime("%b %d, %Y %I:%M %p")
    except Exception:
        return dt_str  # fallback to original if parsing fails

def update_history_text(scrolled_text):
    from ai_space_weather.ai_model import resource_path  # if not already imported
    data_file = resource_path("data/space_weather_data.json")
    if not os.path.exists(data_file):
        scrolled_text.delete("1.0", tk.END)
        scrolled_text.insert(tk.END, "No data available.")
        return

    try:
        with open(data_file, "r") as f:
            data = json.load(f)

        # Format the "Last Updated" timestamp
        last_updated_raw = data.get("timestamp", "Unknown")
        if last_updated_raw != "Unknown":
            last_updated = format_datetime(last_updated_raw)
        else:
            last_updated = "Unknown"

        # Solar flares (format beginTime)
        solar_flares = data.get("solar_flares", [])
        solar_flares_text = "\n".join([
            f"{flare.get('classType', 'Unknown')} at {format_datetime(flare.get('beginTime', 'Unknown'))}, Duration: {flare.get('duration', 'N/A')}s"
            for flare in solar_flares[-5:]
        ])

        # Geomagnetic Storms (format startTime)
        geo_storms = data.get("geomagnetic_storms", [])
        geo_storms_text = "\n".join([
            f"Storm Level {storm.get('kpIndex', 'N/A')} at {format_datetime(storm.get('startTime', 'Unknown'))}"
            for storm in geo_storms[-3:]
        ])

        # CME Events (format startTime)
        cme_events = data.get("coronal_mass_ejections", [])
        cme_text = "\n".join([
            f"Speed: {cme.get('speed', 'N/A')} km/s, Type: {cme.get('type', 'N/A')} at {format_datetime(cme.get('startTime', 'Unknown'))}"
            for cme in cme_events[-3:]
        ])

        # SEP Events (format eventTime)
        sep_events = data.get("solar_energetic_particles", [])
        sep_text = "\n".join([
            f"Source: {sep.get('source', 'N/A')} at {format_datetime(sep.get('eventTime', 'Unknown'))}"
            for sep in sep_events[-3:]
        ])

        # IPS Events (format eventTime)
        ips_events = data.get("interplanetary_shocks", [])
        ips_text = "\n".join([
            f"Location: {ips.get('location', 'N/A')} at {format_datetime(ips.get('eventTime', 'Unknown'))}"
            for ips in ips_events[-3:]
        ])

        # Upcoming Events (format predictedTime)
        upcoming_events = data.get("upcoming_events", [])
        if upcoming_events:
            upcoming_text = "\n".join([
                f"{event.get('type', 'Unknown Event')} expected at {format_datetime(event.get('predictedTime', 'Unknown'))}"
                for event in upcoming_events
            ])
        else:
            upcoming_text = "No upcoming solar events."

        # AI Prediction and Past Predictions
        from ai_space_weather.ai_model import predict_next_solar_event, load_past_predictions
        ai_prediction = predict_next_solar_event()
        past_predictions = load_past_predictions()

        full_text = (
            f"Last Updated: {last_updated}\n\n"
            "=== Recent Solar Flares ===\n" + (solar_flares_text or "No recent solar flares.") + "\n\n"
            "=== Geomagnetic Storms ===\n" + (geo_storms_text or "No recent geomagnetic storms.") + "\n\n"
            "=== CME Events ===\n" + (cme_text or "No recent CMEs.") + "\n\n"
            "=== SEP Events ===\n" + (sep_text or "No recent SEP events.") + "\n\n"
            "=== IPS Events ===\n" + (ips_text or "No recent IPS events.") + "\n\n"
            "=== Upcoming Events ===\n" + upcoming_text + "\n\n"
            "=== AI Prediction ===\n" + ai_prediction + "\n\n"
            "=== Past Predictions ===\n" + past_predictions
        )

        scrolled_text.delete("1.0", tk.END)
        scrolled_text.insert(tk.END, full_text)

    except Exception as e:
        scrolled_text.delete("1.0", tk.END)
        scrolled_text.insert(tk.END, f"Error loading data: {e}")

def start_history_updates(scrolled_text):
    def auto_update():
        while True:
            update_history_text(scrolled_text)
            time.sleep(1800)
    t = threading.Thread(target=auto_update, daemon=True)
    t.start()

# ---------------------------------------
# Main UI
# ---------------------------------------
def main():
    root = tk.Tk()
    root.title("AI Space Weather Monitor")
    root.geometry("1000x700")

    # Dark style for the Notebook and general frames/labels
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TNotebook", background="#2b2b2b")
    style.configure("TNotebook.Tab", font=("Helvetica", 12, "bold"), padding=[10, 5])
    style.configure("TFrame", background="#2b2b2b")
    style.configure("TLabel", background="#2b2b2b", foreground="white", font=("Helvetica", 11))

    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True)

    # --- Prediction tab (Dark Themed) ---
    prediction_tab = ttk.Frame(notebook)
    notebook.add(prediction_tab, text="Prediction")

    # Canvas fills entire prediction tab with black background
    pred_canvas = tk.Canvas(prediction_tab, bg="black")
    pred_canvas.pack(fill="both", expand=True)

    def init_prediction_tab():
        start_prediction_animation(pred_canvas)
    root.after(100, init_prediction_tab)

    # --- History tab (White Background) ---
    # We'll manually set the background to white for this tab's frame and content
    history_tab = ttk.Frame(notebook)
    # Force the background color to white for this frame
    history_tab.configure(style="White.TFrame")  
    # We'll define a custom style for frames that we want white
    style.configure("White.TFrame", background="white")

    notebook.add(history_tab, text="History")

    # A scrolled text widget with white bg and black fg
    history_text = ScrolledText(history_tab, wrap="word", width=80, height=25, bg="white", fg="black", font=("Helvetica", 11))
    history_text.pack(fill="both", expand=True, padx=10, pady=10)

    # Load the data
    update_history_text(history_text)
    start_history_updates(history_text)

    root.mainloop()

if __name__ == "__main__":
    main()
