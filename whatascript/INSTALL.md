# Auto-Start Setup Instructions

## Option 1: Systemd Service (Recommended)

This will run the display as a system service that starts automatically on boot.

### Installation Steps:

1. **Copy the service file:**
```bash
sudo cp whataburger-display.service /etc/systemd/system/
```

2. **Reload systemd:**
```bash
sudo systemctl daemon-reload
```

3. **Enable the service to start on boot:**
```bash
sudo systemctl enable whataburger-display.service
```

4. **Start the service now:**
```bash
sudo systemctl start whataburger-display.service
```

### Managing the Service:

**Check status:**
```bash
sudo systemctl status whataburger-display.service
```

**View logs:**
```bash
sudo journalctl -u whataburger-display.service -f
```

**Stop the service:**
```bash
sudo systemctl stop whataburger-display.service
```

**Restart the service:**
```bash
sudo systemctl restart whataburger-display.service
```

**Disable auto-start:**
```bash
sudo systemctl disable whataburger-display.service
```

---

## Option 2: Cron Job (Alternative)

Add to crontab to run on reboot.

1. **Edit crontab:**
```bash
crontab -e
```

2. **Add this line:**
```
@reboot sleep 30 && cd /home/admin/WhataBurgerMenu/whatascript && /usr/bin/python3 whatascript.py > /tmp/whataburger.log 2>&1
```

3. **Save and exit**

---

## Option 3: rc.local (Legacy)

For older systems using rc.local:

1. **Edit rc.local:**
```bash
sudo nano /etc/rc.local
```

2. **Add before `exit 0`:**
```bash
cd /home/admin/WhataBurgerMenu/whatascript && /usr/bin/python3 whatascript.py &
```

3. **Make it executable:**
```bash
sudo chmod +x /etc/rc.local
```

---

## Troubleshooting

**Service won't start:**
- Check logs: `sudo journalctl -u whataburger-display.service`
- Verify Python path: `which python3`
- Test manually: `cd ~/WhataBurgerMenu/whatascript && sudo python3 whatascript.py`

**Display not showing:**
- Ensure SPI is enabled: `sudo raspi-config` → Interface Options → SPI
- Check hardware connections
- Verify LCD module works with test script

**Service crashes:**
- Check network connectivity (needed for weather/calendar)
- Verify API keys are configured correctly
