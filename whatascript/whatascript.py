#!/usr/bin/python
# -*- coding: UTF-8 -*-
import os
import sys 
import time
import logging
import spidev as SPI
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

UPDATE_INTERVAL = 60  # Update weather/calendar every 60 seconds
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
    header_text = "TIME & DATE"
    bbox = draw.textbbox((0, 0), header_text, font=font_small)
    header_width = bbox[2] - bbox[0]
    draw.text(((disp.width - header_width) // 2, 10), header_text, fill=COLOR_GRAY, font=font_small)
    
    # Day of week
    day_text = now.strftime('%A')
    bbox = draw.textbbox((0, 0), day_text, font=font_large)
    day_width = bbox[2] - bbox[0]
    draw.text(((disp.width - day_width) // 2, 40), day_text, fill=COLOR_ORANGE, font=font_large)
    
    # Date
    date_text = now.strftime('%B %d, %Y')
    bbox = draw.textbbox((0, 0), date_text, font=font_medium)
    date_width = bbox[2] - bbox[0]
    draw.text(((disp.width - date_width) // 2, 80), date_text, fill=COLOR_WHITE, font=font_medium)
    
    # Time - Large display
    time_text = now.strftime('%I:%M')
    bbox = draw.textbbox((0, 0), time_text, font=font_large)
    time_width = bbox[2] - bbox[0]
    draw.text(((disp.width - time_width) // 2, 130), time_text, fill=COLOR_ORANGE, font=font_large)
    
    # Seconds
    sec_text = now.strftime('%S')
    bbox = draw.textbbox((0, 0), sec_text, font=font_medium)
    sec_width = bbox[2] - bbox[0]
    draw.text(((disp.width - sec_width) // 2, 175), sec_text, fill=COLOR_GRAY, font=font_medium)
    
    # AM/PM
    ampm_text = now.strftime('%p')
    bbox = draw.textbbox((0, 0), ampm_text, font=font_medium)
    ampm_width = bbox[2] - bbox[0]
    draw.text(((disp.width - ampm_width) // 2, 200), ampm_text, fill=COLOR_WHITE, font=font_medium)
    
    # Mini weather preview if available
    if weather_data:
        temp_c = weather_data['temp']
        temp_f = temp_c * 9/5 + 32
        temp_text = f"{temp_f:.0f}°F / {temp_c:.0f}°C"
        bbox = draw.textbbox((0, 0), temp_text, font=font_small)
        temp_width = bbox[2] - bbox[0]
        draw.text(((disp.width - temp_width) // 2, 240), temp_text, fill=COLOR_LIGHT_BLUE, font=font_small)
        
        cond_text = weather_data['condition']
        bbox = draw.textbbox((0, 0), cond_text, font=font_small)
        cond_width = bbox[2] - bbox[0]
        draw.text(((disp.width - cond_width) // 2, 260), cond_text, fill=COLOR_LIGHT_BLUE, font=font_small)
    
    return image

# ============================================================
#  Display Functions - Weather View
# ============================================================
def draw_view_weather(disp, font_large, font_medium, font_small):
    """Display Weather view"""
    image = Image.new("RGB", (disp.width, disp.height), COLOR_BLACK)
    draw = ImageDraw.Draw(image)
    
    # Header
    header_text = "WEATHER"
    bbox = draw.textbbox((0, 0), header_text, font=font_small)
    header_width = bbox[2] - bbox[0]
    draw.text(((disp.width - header_width) // 2, 10), header_text, fill=COLOR_GRAY, font=font_small)
    
    if weather_data is None:
        error_text = "No weather data"
        bbox = draw.textbbox((0, 0), error_text, font=font_medium)
        error_width = bbox[2] - bbox[0]
        draw.text(((disp.width - error_width) // 2, 60), error_text, fill=COLOR_RED, font=font_medium)
        
        check_text = "Check API key"
        bbox = draw.textbbox((0, 0), check_text, font=font_small)
        check_width = bbox[2] - bbox[0]
        draw.text(((disp.width - check_width) // 2, 90), check_text, fill=COLOR_RED, font=font_small)
        
        conn_text = "and connection"
        bbox = draw.textbbox((0, 0), conn_text, font=font_small)
        conn_width = bbox[2] - bbox[0]
        draw.text(((disp.width - conn_width) // 2, 110), conn_text, fill=COLOR_RED, font=font_small)
        return image
    
    # Temperature - Large (show both F and C)
    temp_c = weather_data['temp']
    temp_f = temp_c * 9/5 + 32
    temp_text = f"{temp_f:.0f}°F"
    bbox = draw.textbbox((0, 0), temp_text, font=font_large)
    temp_width = bbox[2] - bbox[0]
    draw.text(((disp.width - temp_width) // 2, 40), temp_text, fill=COLOR_ORANGE, font=font_large)
    
    # Celsius below
    temp_c_text = f"{temp_c:.0f}°C"
    bbox = draw.textbbox((0, 0), temp_c_text, font=font_medium)
    tempc_width = bbox[2] - bbox[0]
    draw.text(((disp.width - tempc_width) // 2, 85), temp_c_text, fill=COLOR_GRAY, font=font_medium)
    
    # Condition
    condition_text = weather_data['condition']
    bbox = draw.textbbox((0, 0), condition_text, font=font_medium)
    cond_width = bbox[2] - bbox[0]
    draw.text(((disp.width - cond_width) // 2, 115), condition_text, fill=COLOR_WHITE, font=font_medium)
    
    # Description
    desc_text = weather_data['description'].title()
    bbox = draw.textbbox((0, 0), desc_text, font=font_small)
    desc_width = bbox[2] - bbox[0]
    draw.text(((disp.width - desc_width) // 2, 145), desc_text, fill=COLOR_GRAY, font=font_small)
    
    # Details box
    y_offset = 180
    details_text = "Details:"
    bbox = draw.textbbox((0, 0), details_text, font=font_small)
    details_width = bbox[2] - bbox[0]
    draw.text(((disp.width - details_width) // 2, y_offset), details_text, fill=COLOR_LIGHT_BLUE, font=font_small)
    
    y_offset += 25
    feels_c = weather_data['feels_like']
    feels_f = feels_c * 9/5 + 32
    feels_text = f"Feels: {feels_f:.0f}°F / {feels_c:.0f}°C"
    bbox = draw.textbbox((0, 0), feels_text, font=font_small)
    feels_width = bbox[2] - bbox[0]
    draw.text(((disp.width - feels_width) // 2, y_offset), feels_text, fill=COLOR_WHITE, font=font_small)
    
    y_offset += 20
    humid_text = f"Humidity: {weather_data['humidity']}%"
    bbox = draw.textbbox((0, 0), humid_text, font=font_small)
    humid_width = bbox[2] - bbox[0]
    draw.text(((disp.width - humid_width) // 2, y_offset), humid_text, fill=COLOR_WHITE, font=font_small)
    
    y_offset += 20
    wind_text = f"Wind: {weather_data['wind_speed']:.1f} m/s"
    bbox = draw.textbbox((0, 0), wind_text, font=font_small)
    wind_width = bbox[2] - bbox[0]
    draw.text(((disp.width - wind_width) // 2, y_offset), wind_text, fill=COLOR_WHITE, font=font_small)
    
    # Update time
    now = datetime.now()
    time_text = f"Updated: {now.strftime('%I:%M %p')}"
    bbox = draw.textbbox((0, 0), time_text, font=font_small)
    time_width = bbox[2] - bbox[0]
    draw.text(((disp.width - time_width) // 2, 250), time_text, fill=COLOR_GRAY, font=font_small)
    
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
            # Try Font02 for cleaner, more readable text
            font_path = os.path.join(os.path.dirname(__file__), 'Font/Font02.ttf')
            font_large = ImageFont.truetype(font_path, 35)
            font_medium = ImageFont.truetype(font_path, 20)
            font_small = ImageFont.truetype(font_path, 14)
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
