from flask import Flask, render_template, request, redirect
import requests
import os

app = Flask(__name__)
NOTES_FILE = "notes.txt"

def load_notes():
    if not os.path.exists(NOTES_FILE):
        return []
    with open(NOTES_FILE, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def save_notes(notes):
    with open(NOTES_FILE, "w", encoding="utf-8") as f:
        for note in notes:
            f.write(note + "\n")

def get_city_weather(city_name):
    # 1. Look up coordinates for the city
    geo_site = "https://geocoding-api." + "open-meteo.com" + "/v1/search"
    geo_data = requests.get(geo_site, params={"name": city_name, "count": 1}).json()
    
    if "results" not in geo_data:
        return city_name, "City not found"
        
    place = geo_data["results"][0]
    lat, lon = place["latitude"], place["longitude"]
    display_name = f"{place['name']}, {place.get('country', '')}"
    
    # 2. Fetch live weather for those coordinates
    weather_site = "https://api." + "open-meteo.com" + "/v1/forecast"
    params = {"latitude": lat, "longitude": lon, "current_weather": True}
    temp = requests.get(weather_site, params=params).json()["current_weather"]["temperature"]
    return display_name, f"{temp}°C"

@app.route("/", methods=["GET", "POST"])
def home():
    money_site = "https://open." + "er-api.com" + "/v6/latest/USD"
    kes = requests.get(money_site).json()["rates"]["KES"]

    converted_text = ""
    city = "Nyahururu"

    if request.method == "POST":
        if "usd" in request.form:
            usd = float(request.form.get("usd", 0))
            converted_text = f"{usd} USD = {usd * kes:,.2f} KES"
        if "city" in request.form and request.form.get("city").strip():
            city = request.form.get("city").strip()

    city_label, weather_text = get_city_weather(city)

    news_site = "https://hacker-news." + "firebaseio.com" + "/v0/topstories.json"
    story_ids = requests.get(news_site).json()[:3]
    stories = []
    for sid in story_ids:
        item_site = "https://hacker-news." + "firebaseio.com" + f"/v0/item/{sid}.json"
        data = requests.get(item_site).json()
        stories.append({
            "title": data.get("title"),
            "url": data.get("url", f"https://ycombinator.com{sid}")
        })

    return render_template(
        "index.html",
        kes=f"{kes:.2f}",
        converted_text=converted_text,
        city_label=city_label,
        weather_text=weather_text,
        stories=stories
    )

@app.route("/notes", methods=["GET", "POST"])
def notes():
    notes_list = load_notes()
    if request.method == "POST":
        new_note = request.form.get("note")
        if new_note:
            notes_list.append(new_note)
            save_notes(notes_list)
        return redirect("/notes")
    return render_template("notes.html", notes_list=notes_list)

@app.route("/delete/<int:index>", methods=["POST"])
def delete_note(index):
    notes_list = load_notes()
    if 0 <= index < len(notes_list):
        notes_list.pop(index)
        save_notes(notes_list)
    return redirect("/notes")

if __name__ == "__main__":
    app.run(debug=True)
