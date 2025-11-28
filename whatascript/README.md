# WhataBurger Menu Display

A Raspberry Pi project that displays time, weather, and calendar information on a 1.69" LCD screen.

## Features

- **Time & Date View**: Large clock display with current date
- **Weather View**: Real-time weather from OpenWeatherMap API
- **Calendar View**: Upcoming events from Apple iCloud Calendar
- Auto-cycling between views every 10 seconds

## Hardware Requirements

- Raspberry Pi (tested on Pi 3B)
- 1.69" LCD Display (240x280, ST7789 driver)
- SPI connection

## Installation

1. Clone the repository on your Raspberry Pi:
```bash
cd ~
git clone https://github.com/allanquisha/WhataBurgerMenu.git
cd WhataBurgerMenu/whatascript
```

2. Install Python dependencies:
```bash
sudo pip3 install -r requirements.txt
```

3. Enable SPI interface:
```bash
sudo raspi-config
# Navigate to: Interface Options -> SPI -> Enable
```

## Configuration

Edit `whatascript.py` to configure:

1. **Weather API**: Get a free API key from [OpenWeatherMap](https://openweathermap.org/api)
   ```python
   WEATHER_API_KEY = "your_api_key_here"
   CITY_ID = "your_city_id"  # Find at openweathermap.org
   ```

2. **Apple Calendar**: 
   - Go to icloud.com/calendar
   - Click share icon next to your calendar
   - Enable "Public Calendar" and copy the URL
   - Replace `webcal://` with `https://`
   ```python
   APPLE_CALENDAR_URL = "https://p??-caldav.icloud.com/..."
   ```

## Running

```bash
cd ~/WhataBurgerMenu/whatascript
sudo python3 whatascript.py
```

Press `Ctrl+C` to exit.

## Project Structure

```
whatascript/
├── whatascript.py       # Main application
├── lib/                 # LCD driver library
│   ├── LCD_1inch69.py
│   └── lcdconfig.py
├── Font/                # TrueType fonts
│   ├── Font01.ttf
│   └── Font02.ttf
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## Troubleshooting

**"No module named 'lib'" error:**
- Make sure you're running from the `whatascript` directory
- Verify lib folder exists with LCD_1inch69.py inside

**"Permission denied" on GPIO:**
- Always run with `sudo` for GPIO access

**Display not working:**
- Check SPI is enabled: `lsmod | grep spi`
- Verify connections match pin configuration in script
- Test with example code: `cd LCD_Module_RPI_code/RaspberryPi/python/example && sudo python3 1inch69_LCD_test.py`

## License

MIT
