# -*- coding: utf-8 -*-
from tkinter import *
from tkinter import messagebox, simpledialog
from configparser import ConfigParser
from datetime import datetime, timedelta
from PIL import Image, ImageTk
import requests
import os
import smtplib

# Config and API
config_file = "config.ini"
config = ConfigParser()
config.read(config_file, encoding="utf-8")
api_key = config["api_key"]["key"]

# API URLs
weather_url = "https://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={api_key}&units=metric"
forecast_url = "https://api.openweathermap.org/data/2.5/forecast?q={city_name}&appid={api_key}&units=metric"
air_quality_url = "https://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={api_key}"

# City list for suggestions
city_list = [
    "New York", "London", "Paris", "Tokyo", "Berlin", "Moscow", "Beijing", "Sydney",
    "Los Angeles", "Chicago", "Toronto", "Barcelona", "Rome", "Dubai", "Istanbul",
    "Mumbai", "Seoul", "Bangkok", "Cape Town", "Buenos Aires"
]

original_bg_image = None

def update_background(condition):
    global original_bg_image
    condition = condition.lower()
    mapping = {
        "clear": "sunny.jpg",
        "rain": "rainy.jpg",
        "snow": "snowy.jpg",
        "clouds": "cloudy.jpg",
        "mist": "misty.jpg"
    }
    filename = mapping.get(condition)
    if filename:
        try:
            path = os.path.join("background_icon", filename)
            original_bg_image = Image.open(path)
            resize_background()
        except Exception as e:
            print(f"Background error: {e}")

def resize_background(event=None):
    if original_bg_image:
        w = app.winfo_width()
        h = app.winfo_height()
        resized = original_bg_image.resize((w, h), Image.LANCZOS)
        bg_image = ImageTk.PhotoImage(resized)
        background_label.config(image=bg_image)
        background_label.image = bg_image

def get_weather(city):
    result = requests.get(weather_url.format(city_name=city, api_key=api_key))
    if result.status_code == 200:
        json = result.json()
        city = json["name"]
        country = json["sys"]["country"]
        temp_celsius = round(json["main"]["temp"])
        temp_fahrenheit = (temp_celsius * 9 / 5) + 32
        icon = json["weather"][0]["icon"]
        weather = json["weather"][0]["main"]
        humidity = json["main"]["humidity"]
        timezone_offset = json["timezone"]
        local_time = datetime.utcnow() + timedelta(seconds=timezone_offset)
        formatted_time = local_time.strftime("%H:%M:%S")
        lat = json["coord"]["lat"]
        lon = json["coord"]["lon"]
        feels_like = round(json["main"]["feels_like"])
        return (city, country, temp_celsius, temp_fahrenheit, icon, weather, formatted_time, humidity, lat, lon, feels_like)
    else:
        return None

def get_forecast(city):
    result = requests.get(forecast_url.format(city_name=city, api_key=api_key))
    forecast_data = []
    if result.status_code == 200:
        json = result.json()
        list_data = json["list"]
        seen_dates = set()
        for entry in list_data:
            date_txt = entry["dt_txt"].split(" ")[0]
            if date_txt not in seen_dates:
                seen_dates.add(date_txt)
                temp = round(entry["main"]["temp"])
                condition = entry["weather"][0]["main"]
                humidity = entry["main"]["humidity"]
                forecast_data.append((date_txt, temp, condition, humidity))
            if len(forecast_data) >= 3:
                break
    return forecast_data

def get_humanity_advice(weather_condition):
    condition = weather_condition.lower()
    if condition == "rain":
        return "Don't forget your umbrella! ☔"
    elif condition == "clear":
        return "Wear your sunglasses! 😎"
    elif condition == "snow":
        return "Dress warmly! ❄️"
    elif condition == "clouds":
        return "Cloudy day ahead, stay cheerful! ☁"
    else:
        return "Be ready for anything! 🌈"

def get_air_quality(city):
    weather = get_weather(city)
    if weather:
        lat = weather[8]
        lon = weather[9]
        result = requests.get(air_quality_url.format(lat=lat, lon=lon, api_key=api_key))
        if result.status_code == 200:
            json = result.json()
            aqi = json["list"][0]["main"]["aqi"]
            return get_air_quality_text(aqi)
    return "Air quality information unavailable."

def get_air_quality_text(aqi):
    return {
        1: "Good air quality (AQI: 1).",
        2: "Fair air quality (AQI: 2).",
        3: "Moderate air quality (AQI: 3).",
        4: "Poor air quality (AQI: 4).",
        5: "Very poor air quality (AQI: 5)."
    }.get(aqi, "Unknown air quality.")

def predict_weather(forecast):
    if not forecast:
        return "No forecast available."
    temps = [temp for (_, temp, _, _) in forecast]
    avg_temp = sum(temps) / len(temps)
    conditions = [condition for (_, _, condition, _) in forecast]
    most_common_condition = max(set(conditions), key=conditions.count)
    return f"Forecast: {round(avg_temp)}°C, {most_common_condition}."

def search(event=None):
    city = city_text.get()
    if city_suggestions_listbox.winfo_ismapped():
        city_suggestions_listbox.place_forget()

    weather = get_weather(city)
    forecast = get_forecast(city)

    if weather:
        update_background(weather[5])
        location_lbl.config(text=f"{weather[0]}, {weather[1]}")
        temp_lbl.config(text=f"{weather[2]}°C, {weather[3]:.2f}°F")
        feels_like_lbl.config(text=f"Feels Like: {weather[10]}°C")
        weather_lbl.config(text=weather[5])
        time_lbl.config(text=f"Local Time: {weather[6]}")
        humidity_lbl.config(text=f"Humidity: {weather[7]}%")
        reminder_lbl.config(text=get_humanity_advice(weather[5]))

        try:
            img = PhotoImage(file=f"C:/Users/damla/PycharmProjects/Weather/weather_icons/{weather[4]}.png")
            image.config(image=img)
            image.image = img
        except Exception as e:
            print(f"Image loading error: {e}")

        if forecast:
            forecast_text = ""
            for date, temp, condition, humidity in forecast:
                forecast_text += f"{date}: {temp}°C, {condition}, Humidity: {humidity}%\n"
            forecast_lbl.config(text=forecast_text)
            prediction_lbl.config(text=predict_weather(forecast))

        air_quality = get_air_quality(city)
        air_quality_lbl.config(text=air_quality)

    else:
        messagebox.showerror("Error", f"{city} not found.")

def on_keyrelease(event):
    value = event.widget.get().strip().lower()
    if value == '':
        city_suggestions_listbox.place_forget()
    else:
        data = [item for item in city_list if value in item.lower()]
        update_suggestions(data)

def update_suggestions(data):
    if data:
        city_suggestions_listbox.delete(0, END)
        for item in data:
            city_suggestions_listbox.insert(END, item)
        city_suggestions_listbox.place(x=city_entry.winfo_x(), y=city_entry.winfo_y() + city_entry.winfo_height())
    else:
        city_suggestions_listbox.place_forget()

def on_suggestion_click(event):
    selection = event.widget.curselection()
    if selection:
        index = selection[0]
        selected_city = event.widget.get(index)
        city_text.set(selected_city)
        city_suggestions_listbox.place_forget()
        search()

def send_weather_email():
    sender_email = simpledialog.askstring("Sender Email", "Enter sender email address:")
    receiver_email = simpledialog.askstring("Recipient Email", "Enter recipient email address:")
    subject = simpledialog.askstring("Subject", "Enter email subject:")

    if not all([sender_email, receiver_email, subject]):
        messagebox.showwarning("Missing Info", "Please fill all fields.")
        return

    password = "eglp uliq jsst ryoa"

    location = location_lbl.cget("text")
    temperature = temp_lbl.cget("text")
    feels_like = feels_like_lbl.cget("text")
    weather_text = weather_lbl.cget("text")
    time = time_lbl.cget("text")
    humidity = humidity_lbl.cget("text")
    forecast = forecast_lbl.cget("text")
    prediction = prediction_lbl.cget("text")
    air_quality = air_quality_lbl.cget("text")
    advice = reminder_lbl.cget("text")

    body = f"""Current Weather Info:

Location: {location}
Temperature: {temperature}
{feels_like}
Weather: {weather_text}
{time}
{humidity}

Air Quality: {air_quality}

Forecast:
{forecast}

{prediction}

Advice: {advice}
"""

    email_text = f"Subject: {subject}\n\n{body}"

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, email_text.encode("utf-8"))
        server.quit()
        messagebox.showinfo("Success", f"Weather information sent to {receiver_email}.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to send email:\n{e}")

def get_current_location_city():
    try:
        response = requests.get("https://ipinfo.io/json")
        if response.status_code == 200:
            data = response.json()
            return data.get("city", "")
    except Exception as e:
        print(f"IP location error: {e}")
    return ""

def fetch_current_location_weather():
    current_city = get_current_location_city()
    if current_city:
        city_text.set(current_city)
        search()
    else:
        messagebox.showerror("Error", "Could not detect your location.")

# UI Setup
app = Tk()
app.title("Weather App")
app.geometry("700x650")
app.bind("<Configure>", resize_background)

background_label = Label(app)
background_label.place(x=0, y=0, relwidth=1, relheight=1)

city_text = StringVar()
city_entry = Entry(app, textvariable=city_text, font=("Arial", 14), bg="white", fg="black", bd=2)
city_entry.pack(pady=10, padx=10, fill=X)
city_entry.bind("<KeyRelease>", on_keyrelease)
city_entry.bind("<Return>", search)

city_suggestions_listbox = Listbox(app, height=5, font=("Arial", 12))
city_suggestions_listbox.bind("<<ListboxSelect>>", on_suggestion_click)

search_btn = Button(app, text="Search Weather", width=20, command=search, bg="#BBDEFB", fg="#0D47A1", font=("Arial", 12))
search_btn.pack(pady=5)

current_loc_btn = Button(app, text="Şu Anki Konum", width=20, command=fetch_current_location_weather, bg="#FFE082", fg="#E65100", font=("Arial", 12))
current_loc_btn.pack(pady=5)

send_email_btn = Button(app, text="Send via Email", width=20, command=send_weather_email, bg="#C8E6C9", fg="#1B5E20", font=("Arial", 12))
send_email_btn.pack(pady=5)

location_lbl = Label(app, text="Location", font=("Arial", 20, "bold"), bg="#E3F2FD", fg="#0D47A1")
location_lbl.pack()

image = Label(app, bg="#E3F2FD")
image.pack()

temp_lbl = Label(app, text="Temperature", font=("Arial", 16), bg="#E3F2FD", fg="#0D47A1")
temp_lbl.pack()

feels_like_lbl = Label(app, text="Feels Like: --°C", font=("Arial", 14), bg="#E3F2FD", fg="#0D47A1")
feels_like_lbl.pack()

weather_lbl = Label(app, text="Weather", font=("Arial", 16), bg="#E3F2FD", fg="#0D47A1")
weather_lbl.pack()

time_lbl = Label(app, text="Local Time: --:--:--", font=("Arial", 14), bg="#E3F2FD", fg="#0D47A1")
time_lbl.pack()

humidity_lbl = Label(app, text="Humidity: --%", font=("Arial", 14), bg="#E3F2FD", fg="#0D47A1")
humidity_lbl.pack()

forecast_lbl = Label(app, text="", font=("Arial", 12), bg="#E3F2FD", fg="#0D47A1", justify="left")
forecast_lbl.pack(pady=10)

prediction_lbl = Label(app, text="", font=("Arial", 14, "italic"), bg="#E3F2FD", fg="#0D47A1", wraplength=600, justify="center")
prediction_lbl.pack(pady=10)

air_quality_lbl = Label(app, text="Air Quality", font=("Arial", 14), bg="#E3F2FD", fg="#0D47A1")
air_quality_lbl.pack(pady=10)

reminder_lbl = Label(app, text="", font=("Arial", 14, "italic"), bg="#E3F2FD", fg="#0D47A1", wraplength=600, justify="center")
reminder_lbl.pack(pady=10)

app.mainloop()
