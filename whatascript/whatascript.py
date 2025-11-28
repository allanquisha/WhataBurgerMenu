#!/usr/bin/python
# -*- coding: UTF-8 -*-
#import chardet
import os
import sys 
import time
import logging
import spidev as SPI
sys.path.append("..")
from lib import LCD_1inch69
from PIL import Image, ImageDraw, ImageFont

# Raspberry Pi pin configuration:
RST = 27
DC = 25
BL = 18
bus = 0 
device = 0 
logging.basicConfig(level = logging.DEBUG)

import requests
from datetime import datetime
import calendar
from enum import Enum


# display with hardware SPI:
''' Warning!!!Don't  creation of multiple displayer objects!!! '''
#disp = LCD_1inch69.LCD_1inch69(spi=SPI.SpiDev(bus, device),spi_freq=10000000,rst=RST,dc=DC,bl=BL)
disp = LCD_1inch69.LCD_1inch69()
# Initialize library.
disp.Init()
# Clear display.
disp.clear()
#Set the backlight to 100
disp.bl_DutyCycle(50)


# --- Configuration ---
WEATHER_API_KEY = "9442039f6bf3a3f641153f7ce2ed46e4"
CITY_ID = "4466033"
UNITS = "metric"
CALENDAR_URL = "YOUR_APPLE_CALENDAR_URL"

# Display dimensions
DISPLAY_WIDTH = 240
DISPLAY_HEIGHT = 280

# --- Color Definitions (RGB) ---
COLOR_BLACK = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_ORANGE = (255, 165, 0)
COLOR_GREEN = (0, 255, 0)
COLOR_RED = (255, 0, 0)
COLOR_BLUE = (0, 0, 255)
COLOR_YELLOW = (255, 255, 0)

# --- View State ---
class ViewState(Enum):
    VIEW_TIME = 0
    VIEW_WEATHER = 1
    VIEW_CALENDAR = 2

# --- Calendar Event Class ---
class CalendarEvent:
    def __init__(self, year, month, day, summary):
        self.year = year
        self.month = month
        self.day = day
        self.summary = summary

# ============================================================
#  Weather Calendar Display Class
# ============================================================
class WeatherCalendarDisplay:
    def __init__(self, disp):
        """
        Initialize display with a display object
        
        Args:
            disp: Display object with methods:
                  - display(image): Display PIL Image on screen
                  - width, height: Display dimensions
        """
        self.disp = disp
        self.width = getattr(disp, 'width', DISPLAY_WIDTH)
        self.height = getattr(disp, 'height', DISPLAY_HEIGHT)
        
        self.current_view = ViewState.VIEW_TIME
        self.weather_condition_main = "Clear"
        self.events = []
        self.last_update = 0
        
        # Try to load fonts
        try:
            self.font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
            self.font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
            self.font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
        except:
            # Fallback to default font
            self.font_large = ImageFont.load_default()
            self.font_medium = ImageFont.load_default()
            self.font_small = ImageFont.load_default()
        
        # Initialize data
        self.fetch_apple_calendar()
        self.weather_text = ""

    # ============================================================
    #  Weather Fetch
    # ============================================================
    def get_weather_description(self):
        try:
            url = f"https://api.openweathermap.org/data/2.5/weather?id={CITY_ID}&units={UNITS}&appid={WEATHER_API_KEY}"
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                return "Weather Error"
            
            data = response.json()
            self.weather_condition_main = data["weather"][0]["main"]
            temp = data["main"]["temp"]
            
            return f"{self.weather_condition_main}, {temp:.1f}°C"
        except Exception as e:
            print(f"Weather fetch error: {e}")
            return "Weather Error"

    # ============================================================
    #  Apple Calendar Fetch
    # ============================================================
    def fetch_apple_calendar(self):
        try:
            response = requests.get(CALENDAR_URL, timeout=10)
            if response.status_code != 200:
                return
            
            payload = response.text
            self.events.clear()
            
            idx = 0
            while True:
                idx = payload.find("BEGIN:VEVENT", idx)
                if idx == -1:
                    break
                
                dtstart_pos = payload.find("DTSTART:", idx)
                summary_pos = payload.find("SUMMARY:", idx)
                
                if dtstart_pos == -1:
                    break
                
                # Extract date string
                date_end = payload.find("\n", dtstart_pos)
                date_str = payload[dtstart_pos + 8:date_end].strip()
                
                # Parse date
                year = int(date_str[0:4])
                month = int(date_str[4:6])
                day = int(date_str[6:8])
                
                # Extract summary
                summary = ""
                if summary_pos != -1:
                    summary_end = payload.find("\n", summary_pos)
                    summary = payload[summary_pos + 8:summary_end].strip()
                
                event = CalendarEvent(year, month, day, summary)
                self.events.append(event)
                
                idx += 10
                
        except Exception as e:
            print(f"Calendar fetch error: {e}")

    # ============================================================
    #  Calendar Helper Functions
    # ============================================================
    def get_day_of_week(self, year, month, day):
        """Returns day of week (0=Sun, 1=Mon, ..., 6=Sat)"""
        m = month
        y = year
        if m < 3:
            m += 12
            y -= 1
        k = y % 100
        j = y // 100
        return (day + 13 * (m + 1) // 5 + k + k // 4 + j // 4 + 5 * j + 5) % 7

    # ============================================================
    #  Display Views
    # ============================================================
    def display_time_view(self):
        """Display current time"""
        image = Image.new('RGB', (self.width, self.height), COLOR_BLACK)
        draw = ImageDraw.Draw(image)
        
        now = datetime.now()
        
        # Draw date
        date_text = now.strftime('%Y-%m-%d')
        draw.text((10, 20), date_text, font=self.font_large, fill=COLOR_ORANGE)
        
        # Draw time
        time_text = now.strftime('%H:%M:%S')
        draw.text((10, 60), f"Time: {time_text}", font=self.font_large, fill=COLOR_ORANGE)
        
        # Display the image
        self.disp.display(image)

    def display_weather_view(self):
        """Display weather information"""
        image = Image.new('RGB', (self.width, self.height), COLOR_BLACK)
        draw = ImageDraw.Draw(image)
        
        # Fetch weather if not already cached
        if not self.weather_text:
            self.weather_text = self.get_weather_description()
        
        now = datetime.now()
        hour = now.hour
        is_night = hour < 6 or hour > 18
        
        # Draw weather label
        draw.text((10, 20), "Weather:", font=self.font_medium, fill=COLOR_ORANGE)
        
        # Draw weather info
        draw.text((10, 45), self.weather_text, font=self.font_medium, fill=COLOR_ORANGE)
        
        # Draw weather icon (text-based)
        icon_map = {
            "Clear": "☀" if not is_night else "☾",
            "Clouds": "☁",
            "Rain": "☂",
            "Snow": "❄",
            "Thunderstorm": "⚡",
            "Mist": "≋",
            "Fog": "≋"
        }
        icon = icon_map.get(self.weather_condition_main, "?")
        
        try:
            # Try to draw icon with large font
            icon_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 48)
            draw.text((160, 20), icon, font=icon_font, fill=COLOR_ORANGE)
        except:
            draw.text((160, 20), icon, font=self.font_large, fill=COLOR_ORANGE)
        
        # Display the image
        self.disp.display(image)

    def display_calendar_view(self):
        """Display calendar"""
        image = Image.new('RGB', (self.width, self.height), COLOR_BLACK)
        draw = ImageDraw.Draw(image)
        
        now = datetime.now()
        year = now.year
        month = now.month
        today = now.day
        
        # Draw month/year header
        header_text = f"{year}-{month:02d}"
        draw.text((10, 10), header_text, font=self.font_large, fill=COLOR_ORANGE)
        
        # Draw day labels
        day_labels = ["S", "M", "T", "W", "T", "F", "S"]
        for i, label in enumerate(day_labels):
            x = i * 32 + 5
            draw.text((x, 40), label, font=self.font_small, fill=COLOR_ORANGE)
        
        # Get calendar data
        days_in_month = calendar.monthrange(year, month)[1]
        start_day = self.get_day_of_week(year, month, 1)
        
        # Draw calendar grid
        x = start_day
        y = 60
        
        for day in range(1, days_in_month + 1):
            xpos = x * 32 + 10
            ypos = y
            
            # Check if this day has an event
            has_event = any(e.year == year and e.month == month and e.day == day 
                          for e in self.events)
            
            # Highlight today
            if day == today:
                draw.rectangle([xpos - 2, ypos - 2, xpos + 24, ypos + 12], 
                             fill=COLOR_WHITE)
                day_color = COLOR_BLACK
            else:
                day_color = COLOR_ORANGE
            
            # Draw day number
            draw.text((xpos, ypos), f"{day:2d}", font=self.font_small, fill=day_color)
            
            # Mark events
            if has_event:
                draw.text((xpos, ypos + 12), "*", font=self.font_small, fill=COLOR_GREEN)
            
            x += 1
            if x > 6:
                x = 0
                y += 24
        
        # Display the image
        self.disp.display(image)

    # ============================================================
    #  Navigation
    # ============================================================
    def next_view(self):
        """Switch to next view"""
        views = list(ViewState)
        idx = views.index(self.current_view)
        self.current_view = views[(idx + 1) % len(views)]
        self.update_display()

    def prev_view(self):
        """Switch to previous view"""
        views = list(ViewState)
        idx = views.index(self.current_view)
        self.current_view = views[(idx - 1) % len(views)]
        self.update_display()

    # ============================================================
    #  Main Update
    # ============================================================
    def update_display(self):
        """Update the current view on display"""
        current_time = time.time()
        
        # Update data every 60 seconds
        if current_time - self.last_update > 60:
            self.last_update = current_time
            if self.current_view == ViewState.VIEW_WEATHER:
                self.weather_text = self.get_weather_description()
            elif self.current_view == ViewState.VIEW_CALENDAR:
                self.fetch_apple_calendar()
        
        # Display current view
        if self.current_view == ViewState.VIEW_TIME:
            self.display_time_view()
        elif self.current_view == ViewState.VIEW_WEATHER:
            self.display_weather_view()
        elif self.current_view == ViewState.VIEW_CALENDAR:
            self.display_calendar_view()

# ============================================================
#  Mock Display Class for Testing
# ============================================================
class MockDisplay:
    """Mock display object for testing without hardware"""
    def __init__(self, width=240, height=240):
        self.width = width
        self.height = height
        self.save_counter = 0
    
    def display(self, image):
        """Display image (saves to file for testing)"""
        # Save image to file for testing
        filename = f"display_output_{self.save_counter}.png"
        image.save(filename)
        print(f"Display updated - saved to {filename}")
        self.save_counter += 1

# ============================================================
#  Example Usage
# ============================================================
def main():
    # Create a mock display (replace with real display object)
    #disp = MockDisplay(width=240, height=240)
    
    # Initialize the weather calendar display
    display = WeatherCalendarDisplay(disp)
    
    print("Weather Calendar Display initialized")
    print("Commands:")
    print("  Press 'n' - Next view")
    print("  Press 'p' - Previous view")
    print("  Press 'q' - Quit")
    
    try:
        while True:
            # Update display
            display.update_display()
            
            # Wait and check for input
            time.sleep(5)
            
            # In a real implementation, you would handle button presses here
            # For now, it just cycles through views automatically
            
    except KeyboardInterrupt:
        print("\nShutting down...")

if __name__ == "__main__":
    main()


