#!/usr/bin/python
# -*- coding: UTF-8 -*-
import os
import sys 
import time
import logging
import spidev as SPI
sys.path.append("..")
from lib import LCD_1inch69
from PIL import Image, ImageDraw, ImageFont
import requests
from datetime import datetime, timedelta
import calendar

# Raspberry Pi pin configuration:
RST = 27
DC = 25
BL = 18
bus = 0 
device = 0 
logging.basicConfig(level = logging.INFO)

# --- Configuration ---
WEATHER_API_KEY = "9442039f6bf3a3f641153f7ce2ed46e4"
CITY_ID = "4466033"  # Change to your city ID
UNITS = "metric"

# Apple Calendar Configuration
# To get your iCloud calendar URL:
# 1. Go to icloud.com/calendar
# 2. Click the share icon next to your calendar
# 3. Enable "Public Calendar" and copy the webcal:// URL
# 4. Replace 'webcal://' with 'https://'
APPLE_CALENDAR_URL = "https://p171-caldav.icloud.com/published/2/MTc5MjIyNjU0MDExNzkyMj6S-vwMDPtCaeXhpF930ZOQhgsgMGIUHZLw0S9J0j3cwSh38Ec0EgVsJh8jstmZg1Y-6skH-eoS3sjY91ZUrDE"

UPDATE_INTERVAL = 300  # Update weather/calendar every 5 minutes
VIEW_CYCLE_TIME = 10  # Seconds to show each view before cycling

# Display dimensions
DISPLAY_WIDTH = 240
DISPLAY_HEIGHT = 280

# View modes
VIEW_TIME = 0
VIEW_WEATHER = 1
VIEW_CALENDAR = 2
TOTAL_VIEWS = 3

# --- Color Definitions (RGB) ---
COLOR_BLACK = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_ORANGE = (255, 165, 0)
COLOR_GREEN = (0, 255, 0)
COLOR_RED = (255, 0, 0)
COLOR_BLUE = (0, 100, 200)
COLOR_YELLOW = (255, 255, 0)
COLOR_GRAY = (128, 128, 128)
COLOR_LIGHT_BLUE = (100, 150, 255)

# Global data cache
weather_data = None
calendar_events = []
current_view = VIEW_TIME
last_data_update = 0

# ============================================================
#  Weather Fetch Function
# ============================================================
def get_weather_data():
    """Fetch weather data from OpenWeatherMap API"""
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?id={CITY_ID}&units={UNITS}&appid={WEATHER_API_KEY}"
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            logging.error(f"Weather API error: {response.status_code}")
            return None
        
        data = response.json()
        weather_info = {
            'condition': data["weather"][0]["main"],
            'description': data["weather"][0]["description"],
            'temp': data["main"]["temp"],
            'feels_like': data["main"]["feels_like"],
            'humidity': data["main"]["humidity"],
            'wind_speed': data["wind"]["speed"] if "wind" in data else 0
        }
        return weather_info
    except Exception as e:
        logging.error(f"Weather fetch error: {e}")
        return None

# ============================================================
#  Apple Calendar Fetch Function
# ============================================================
def parse_ical_date(date_str):
    """Parse iCalendar date format (YYYYMMDD or YYYYMMDDTHHMMSS)"""
    try:
        date_str = date_str.strip()
        if 'T' in date_str:
            # Has time component
            return datetime.strptime(date_str[:15], '%Y%m%dT%H%M%S')
        else:
            # Date only
            return datetime.strptime(date_str[:8], '%Y%m%d')
    except:
        return None

def get_calendar_events():
    """Fetch events from Apple Calendar (iCal format)"""
    if not APPLE_CALENDAR_URL:
        logging.warning("No Apple Calendar URL configured")
        return []
    
    try:
        response = requests.get(APPLE_CALENDAR_URL, timeout=10)
        
        if response.status_code != 200:
            logging.error(f"Calendar API error: {response.status_code}")
            return []
        
        events = []
        lines = response.text.split('\n')
        
        current_event = {}
        in_event = False
        
        for line in lines:
            line = line.strip()
            
            if line == "BEGIN:VEVENT":
                in_event = True
                current_event = {}
            elif line == "END:VEVENT" and in_event:
                in_event = False
                if 'start' in current_event and 'summary' in current_event:
                    events.append(current_event)
            elif in_event:
                if line.startswith("DTSTART"):
                    date_str = line.split(':', 1)[1] if ':' in line else ""
                    dt = parse_ical_date(date_str)
                    if dt:
                        current_event['start'] = dt
                elif line.startswith("SUMMARY:"):
                    current_event['summary'] = line.split(':', 1)[1]
                elif line.startswith("LOCATION:"):
                    current_event['location'] = line.split(':', 1)[1]
        
        # Filter upcoming events (next 7 days)
        now = datetime.now()
        upcoming = [e for e in events if e['start'] >= now and e['start'] <= now + timedelta(days=7)]
        upcoming.sort(key=lambda x: x['start'])
        
        logging.info(f"Found {len(upcoming)} upcoming events")
        return upcoming[:5]  # Return next 5 events
        
    except Exception as e:
        logging.error(f"Calendar fetch error: {e}")
        return []

def update_data():
    """Background function to update weather and calendar data"""
    global weather_data, calendar_events, last_data_update
    
    current_time = time.time()
    if current_time - last_data_update > UPDATE_INTERVAL:
        logging.info("Updating weather and calendar data...")
        weather_data = get_weather_data()
        calendar_events = get_calendar_events()
        last_data_update = current_time

# ============================================================
#  Display Functions - Time View
# ============================================================
def draw_view_time(disp, font_large, font_medium, font_small):
    """Display Time & Date view"""
    image = Image.new("RGB", (disp.width, disp.height), COLOR_BLACK)
    draw = ImageDraw.Draw(image)
    now = datetime.now()
    
    # Header
    draw.text((10, 10), "TIME & DATE", fill=COLOR_GRAY, font=font_small)
    
    # Day of week
    day_text = now.strftime('%A')
    draw.text((10, 40), day_text, fill=COLOR_ORANGE, font=font_large)
    
    # Date
    date_text = now.strftime('%B %d, %Y')
    draw.text((10, 80), date_text, fill=COLOR_WHITE, font=font_medium)
    
    # Time - Large display
    time_text = now.strftime('%I:%M')
    draw.text((10, 130), time_text, fill=COLOR_ORANGE, font=font_large)
    
    # Seconds
    sec_text = now.strftime('%S')
    draw.text((10, 175), sec_text, fill=COLOR_GRAY, font=font_medium)
    
    # AM/PM
    ampm_text = now.strftime('%p')
    draw.text((10, 200), ampm_text, fill=COLOR_WHITE, font=font_medium)
    
    # Mini weather preview if available
    if weather_data:
        temp_text = f"{weather_data['temp']:.0f}°C"
        draw.text((10, 240), temp_text, fill=COLOR_LIGHT_BLUE, font=font_medium)
        draw.text((80, 240), weather_data['condition'], fill=COLOR_LIGHT_BLUE, font=font_small)
    
    return image

# ============================================================
#  Display Functions - Weather View
# ============================================================
def draw_view_weather(disp, font_large, font_medium, font_small):
    """Display Weather view"""
    image = Image.new("RGB", (disp.width, disp.height), COLOR_BLACK)
    draw = ImageDraw.Draw(image)
    
    # Header
    draw.text((10, 10), "WEATHER", fill=COLOR_GRAY, font=font_small)
    
    if weather_data is None:
        draw.text((10, 60), "No weather data", fill=COLOR_RED, font=font_medium)
        draw.text((10, 90), "Check API key", fill=COLOR_RED, font=font_small)
        draw.text((10, 110), "and connection", fill=COLOR_RED, font=font_small)
        return image
    
    # Temperature - Large
    temp_text = f"{weather_data['temp']:.1f}°"
    draw.text((10, 40), temp_text, fill=COLOR_ORANGE, font=font_large)
    
    # Condition
    condition_text = weather_data['condition']
    draw.text((10, 95), condition_text, fill=COLOR_WHITE, font=font_medium)
    
    # Description
    desc_text = weather_data['description'].title()
    draw.text((10, 125), desc_text, fill=COLOR_GRAY, font=font_small)
    
    # Details box
    y_offset = 160
    draw.text((10, y_offset), "Details:", fill=COLOR_LIGHT_BLUE, font=font_small)
    
    y_offset += 25
    feels_text = f"Feels like: {weather_data['feels_like']:.1f}°C"
    draw.text((10, y_offset), feels_text, fill=COLOR_WHITE, font=font_small)
    
    y_offset += 20
    humid_text = f"Humidity: {weather_data['humidity']}%"
    draw.text((10, y_offset), humid_text, fill=COLOR_WHITE, font=font_small)
    
    y_offset += 20
    wind_text = f"Wind: {weather_data['wind_speed']:.1f} m/s"
    draw.text((10, y_offset), wind_text, fill=COLOR_WHITE, font=font_small)
    
    # Update time
    now = datetime.now()
    time_text = f"Updated: {now.strftime('%I:%M %p')}"
    draw.text((10, 250), time_text, fill=COLOR_GRAY, font=font_small)
    
    return image

# ============================================================
#  Display Functions - Calendar View
# ============================================================
def draw_view_calendar(disp, font_large, font_medium, font_small):
    """Display Calendar view with upcoming events"""
    image = Image.new("RGB", (disp.width, disp.height), COLOR_BLACK)
    draw = ImageDraw.Draw(image)
    now = datetime.now()
    
    # Header
    draw.text((10, 10), "UPCOMING EVENTS", fill=COLOR_GRAY, font=font_small)
    
    if not APPLE_CALENDAR_URL:
        draw.text((10, 50), "Calendar not", fill=COLOR_RED, font=font_medium)
        draw.text((10, 75), "configured", fill=COLOR_RED, font=font_medium)
        draw.text((10, 110), "Add your iCloud", fill=COLOR_GRAY, font=font_small)
        draw.text((10, 130), "calendar URL in", fill=COLOR_GRAY, font=font_small)
        draw.text((10, 150), "the script config", fill=COLOR_GRAY, font=font_small)
        return image
    
    if not calendar_events:
        draw.text((10, 50), "No upcoming", fill=COLOR_WHITE, font=font_medium)
        draw.text((10, 75), "events", fill=COLOR_WHITE, font=font_medium)
        
        # Show current date
        date_text = now.strftime('%B %d, %Y')
        draw.text((10, 120), date_text, fill=COLOR_GRAY, font=font_small)
        return image
    
    # Display upcoming events
    y_offset = 40
    for i, event in enumerate(calendar_events[:4]):  # Show max 4 events
        if y_offset > 240:
            break
        
        # Event date
        event_date = event['start']
        if event_date.date() == now.date():
            date_str = "Today"
            date_color = COLOR_ORANGE
        elif event_date.date() == (now + timedelta(days=1)).date():
            date_str = "Tomorrow"
            date_color = COLOR_LIGHT_BLUE
        else:
            date_str = event_date.strftime('%b %d')
            date_color = COLOR_WHITE
        
        # Time
        time_str = event_date.strftime('%I:%M %p')
        
        # Draw event
        draw.text((10, y_offset), date_str, fill=date_color, font=font_small)
        draw.text((80, y_offset), time_str, fill=COLOR_GRAY, font=font_small)
        
        y_offset += 18
        
        # Event title (truncate if too long)
        title = event['summary']
        if len(title) > 25:
            title = title[:22] + "..."
        draw.text((10, y_offset), title, fill=COLOR_WHITE, font=font_small)
        
        y_offset += 25
        
        # Separator line
        if i < len(calendar_events) - 1:
            draw.line([(10, y_offset), (230, y_offset)], fill=COLOR_GRAY, width=1)
            y_offset += 10
    
    return image

# ============================================================
#  Main Display Loop
# ============================================================
def main():
    global current_view, weather_data, calendar_events
    
    try:
        # Initialize display
        logging.info("Initializing display...")
        disp = LCD_1inch69.LCD_1inch69()
        disp.Init()
        disp.clear()
        disp.bl_DutyCycle(50)
        
        # Load fonts
        try:
            font_large = ImageFont.truetype("../Font/Font01.ttf", 40)
            font_medium = ImageFont.truetype("../Font/Font01.ttf", 22)
            font_small = ImageFont.truetype("../Font/Font01.ttf", 16)
        except:
            logging.warning("Could not load custom fonts, using default")
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        # Initial data fetch
        logging.info("Fetching initial data...")
        weather_data = get_weather_data()
        calendar_events = get_calendar_events()
        
        logging.info("="*50)
        logging.info("Display started successfully!")
        logging.info("="*50)
        logging.info("Views will cycle automatically every %d seconds", VIEW_CYCLE_TIME)
        logging.info("View 1: Time & Date")
        logging.info("View 2: Weather")
        logging.info("View 3: Calendar Events")
        logging.info("Press Ctrl+C to exit")
        logging.info("="*50)
        
        last_view_change = time.time()
        frame_count = 0
        
        while True:
            # Update data periodically
            update_data()
            
            # Auto-cycle views
            current_time = time.time()
            if current_time - last_view_change > VIEW_CYCLE_TIME:
                current_view = (current_view + 1) % TOTAL_VIEWS
                last_view_change = current_time
                logging.info("Switching to view %d", current_view + 1)
            
            # Draw current view
            if current_view == VIEW_TIME:
                image = draw_view_time(disp, font_large, font_medium, font_small)
            elif current_view == VIEW_WEATHER:
                image = draw_view_weather(disp, font_large, font_medium, font_small)
            elif current_view == VIEW_CALENDAR:
                image = draw_view_calendar(disp, font_large, font_medium, font_small)
            
            # Display image
            disp.ShowImage(image)
            
            # Update more frequently in time view to show seconds
            if current_view == VIEW_TIME:
                time.sleep(0.5)
            else:
                time.sleep(1)
            
            frame_count += 1
            
    except IOError as e:
        logging.error(f"IOError: {e}")
    except KeyboardInterrupt:
        logging.info("\n" + "="*50)
        logging.info("Shutting down gracefully...")
        logging.info("="*50)
        disp.module_exit()
        exit()
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        disp.module_exit()
        exit()

if __name__ == "__main__":
    main()
