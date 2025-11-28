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

### Option 1: Run Manually
```bash
cd ~/WhataBurgerMenu/whatascript
sudo python3 whatascript.py
```

Press `Ctrl+C` to exit.

### Option 2: Run as Service (Auto-Start on Boot)

**Install the service:**
```bash
cd ~/WhataBurgerMenu/whatascript
sudo cp whataburger-display.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable whataburger-display.service
sudo systemctl start whataburger-display.service
```

**Check status:**
```bash
sudo systemctl status whataburger-display.service
```

Expected output when running successfully:
```
● whataburger-display.service - WhataBurger Menu Display
     Loaded: loaded (/etc/systemd/system/whataburger-display.service; enabled; preset: enabled)
     Active: active (running) since Thu 2025-11-27 23:16:00 CST; 5s ago
   Main PID: 4322 (python3)
      Tasks: 4 (limit: 751)
        CPU: 1.926s
     CGroup: /system.slice/whataburger-display.service
             └─4322 /usr/bin/python3 /home/admin/WhataBurgerMenu/whatascript/whatascript.py

Nov 27 23:16:02 rasp3b-whata python3[4322]: INFO:root:Display started successfully!
Nov 27 23:16:02 rasp3b-whata python3[4322]: INFO:root:==================================================
Nov 27 23:16:02 rasp3b-whata python3[4322]: INFO:root:Views will cycle automatically every 10 seconds
Nov 27 23:16:02 rasp3b-whata python3[4322]: INFO:root:View 1: Time & Date
Nov 27 23:16:02 rasp3b-whata python3[4322]: INFO:root:View 2: Weather
Nov 27 23:16:02 rasp3b-whata python3[4322]: INFO:root:View 3: Calendar Events
Nov 27 23:16:02 rasp3b-whata python3[4322]: INFO:root:Press Ctrl+C to exit
Nov 27 23:16:02 rasp3b-whata python3[4322]: INFO:root:==================================================
```

**Status Indicators:**
- ✅ **Loaded**: Service is installed
- ✅ **Active (running)**: Currently running
- ✅ **Enabled**: Will start automatically on boot

**Service Management Commands:**
```bash
# Stop the service
sudo systemctl stop whataburger-display.service

# Restart the service
sudo systemctl restart whataburger-display.service

# View live logs
sudo journalctl -u whataburger-display.service -f

# Disable auto-start
sudo systemctl disable whataburger-display.service

# Re-enable auto-start
sudo systemctl enable whataburger-display.service
```

## Features

The display automatically:
- ✅ Starts on boot when installed as a service
- ✅ Cycles through time, weather, and calendar views every 10 seconds
- ✅ Updates weather and calendar data every 60 seconds
- ✅ Centers all text with proper margins to prevent edge cutoff
- ✅ Shows temperatures in both Fahrenheit and Celsius
- ✅ Auto-restarts if it crashes (when running as service)

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
