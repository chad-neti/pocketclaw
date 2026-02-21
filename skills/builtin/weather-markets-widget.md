---
name: weather-markets-widget
description: Monitors Polymarket for weather-related prediction markets and shows them on an Android home screen widget with notifications for new markets. Two components - a Termux Node.js monitor (polls Gamma API, sends Android notifications) and a native widget APK (displays active weather markets with Yes%). Filters out NBA/sports false positives. Use when user asks about weather markets, Polymarket weather, weather predictions, temperature markets, or weather betting.
emoji: 🌦️
requires:
  bins:
    - node
tags:
  - polymarket
  - weather
  - prediction-markets
  - widget
  - android
  - notifications
---

# Weather Markets Widget

Monitors Polymarket for weather-related prediction markets and displays them on the Android home screen. Sends Android notifications when new weather markets open. Two components work together:

1. **Termux monitor** (Node.js) — polls the Polymarket Gamma API every 10 minutes, filters for weather markets, sends notifications via `termux-notification`, and serves a local API
2. **Native Android widget** (APK) — reads from the monitor's API and shows weather markets in a scrollable list on the home screen

## What It Shows

- Active weather prediction markets from Polymarket (temperature, hurricane, wildfire, etc.)
- Each market's question and current Yes% price
- Green for >= 50%, orange for < 50%
- Android notification when a new weather market appears
- Auto-refreshes every 10 minutes (monitor) / 30 minutes (widget)

## Requirements

- **Node.js 18+** in Termux (for built-in `fetch`)
- **termux-api** package + Termux:API app (for notifications)
- **Android SDK** build-tools 33+, JDK 17 (for widget APK build)
- Zero npm dependencies

## Architecture

```
Termux (Node.js, port 8788)
  ├── Every 10 min: GET gamma-api.polymarket.com/events
  ├── Filter: weather keywords + sports exclusion
  ├── New market? → termux-notification
  ├── Store seen IDs in ~/.clawphone/skills/weather-markets/seen.json
  └── Serve /api for widget consumption

Native Widget (APK)
  └── GET http://127.0.0.1:8788/api → ListView of weather markets
```

## Part 1: Termux Monitor

### How filtering works

**Weather keyword matching** — multi-word phrases for precision:
- `hurricane season`, `tropical storm`, `highest temperature`, `wildfire`, `drought`, `blizzard`, `flooding`, `polar vortex`, `el nino`, `climate change`, etc.

**Standalone weather words** (unambiguous):
- `hurricane`, `tornado`, `wildfire`, `blizzard`, `drought`, `heatwave`, `snowfall`, `typhoon`, `cyclone`, `monsoon`, `flooding`, `hottest`, `coldest`, `warmest`, `fahrenheit`, `celsius`

**Sports exclusion** — removes false positives from teams with weather names:
- Miami Heat, OKC Thunder, Carolina Hurricanes, St. John's Red Storm, Tulsa Golden Hurricane, etc.
- Also excludes any market containing ` vs `, `nba`, `nhl`, `playoff`, `championship`, etc.

**First-run behavior** — seeds all existing markets as "seen" without sending notifications. Only notifies for genuinely NEW markets discovered on subsequent polls.

### Step 1: Create the monitor

```bash
mkdir -p ~/.clawphone/skills/weather-markets
```

Create `~/.clawphone/skills/weather-markets/monitor.js` — the full monitor server. See the source in `/tmp/weather-monitor.js` or deploy via the setup script below.

### Step 2: Deploy and run

```bash
ADB="/mnt/c/Users/<USER>/Android/Sdk/platform-tools/adb.exe"

cat > /tmp/setup-weather.sh << 'SCRIPT'
#!/data/data/com.termux/files/usr/bin/bash
export HOME=/data/data/com.termux/files/home
export PREFIX=/data/data/com.termux/files/usr
export PATH=$PREFIX/bin:$PATH
mkdir -p ~/.clawphone/skills/weather-markets
pkill -f "node.*monitor.js" 2>/dev/null
sleep 1
cp /data/local/tmp/weather-monitor.js ~/.clawphone/skills/weather-markets/monitor.js
cd ~/.clawphone/skills/weather-markets
nohup node monitor.js > monitor.log 2>&1 &
echo "PID: $!"
SCRIPT

$ADB push /tmp/weather-monitor.js /data/local/tmp/weather-monitor.js
$ADB push /tmp/setup-weather.sh /data/local/tmp/setup-weather.sh
$ADB shell "run-as com.termux cp /data/local/tmp/setup-weather.sh /data/data/com.termux/files/home/setup-weather.sh && \
  run-as com.termux chmod +x /data/data/com.termux/files/home/setup-weather.sh && \
  run-as com.termux /data/data/com.termux/files/usr/bin/bash /data/data/com.termux/files/home/setup-weather.sh"
```

### Step 3: Make it persistent (Termux:Boot)

```bash
mkdir -p ~/.termux/boot
cat > ~/.termux/boot/weather-monitor.sh << 'EOF'
#!/data/data/com.termux/files/usr/bin/sh
termux-wake-lock
node ~/.clawphone/skills/weather-markets/monitor.js &
EOF
chmod +x ~/.termux/boot/weather-monitor.sh
```

### API Endpoints

- `GET http://localhost:8788/` — HTML dashboard with all weather markets
- `GET http://localhost:8788/api` — JSON for the widget

API response:
```json
{
  "markets": [
    {
      "id": "1368948",
      "question": "Will the highest temperature in Seoul be 11°C or higher on February 14?",
      "yesPct": 2,
      "volume24hr": 4805.75,
      "slug": "highest-temperature-in-seoul-on-february-14-2026",
      "startDate": "2026-02-12T11:13:32.730Z",
      "active": true
    }
  ],
  "count": 108,
  "updated": "2026-02-12T16:38:18.854Z"
}
```

## Part 2: Native Android Widget

### Project structure

```
/tmp/weather-widget/
├── AndroidManifest.xml
├── java/com/clawphone/weathermarkets/
│   ├── WeatherWidgetProvider.java
│   └── WeatherWidgetService.java
├── res/
│   ├── layout/widget_layout.xml
│   ├── layout/widget_item.xml
│   ├── values/strings.xml
│   ├── xml/weather_widget_info.xml
│   └── xml/network_security_config.xml
└── rebuild.ps1
```

### Key files

**AndroidManifest.xml** — package `com.clawphone.weathermarkets`, includes:
- `INTERNET` permission
- `networkSecurityConfig` for cleartext localhost access
- `WeatherWidgetProvider` receiver with `APPWIDGET_UPDATE` + custom `REFRESH` action
- `WeatherWidgetService` for populating the ListView

**WeatherWidgetService.java** — `RemoteViewsService` that:
- Fetches from `http://127.0.0.1:8788/api` (the Termux monitor)
- Parses JSON array of markets
- Populates ListView items with question + Yes%
- Green text for >= 50%, orange for < 50%
- Max 8 items displayed

**network_security_config.xml** — allows cleartext HTTP to `localhost`/`127.0.0.1` (required for Android 9+)

### Build

```bash
powershell.exe -ExecutionPolicy Bypass -File '\\wsl.localhost\Ubuntu\tmp\weather-widget\rebuild.ps1'
```

### Add to home screen

1. Long-press empty area on home screen
2. Tap "Widgets"
3. Scroll to "Weather Markets"
4. Tap to expand, long-press and drag the 3x3 preview onto the home screen

### Manual refresh

```bash
adb shell "am broadcast -a com.clawphone.weathermarkets.REFRESH -n com.clawphone.weathermarkets/.WeatherWidgetProvider"
```

## Build Gotchas

Same as other ClawPhone widgets:
- **UNC paths break aapt2/d8** — build script copies to `C:\weather-build`
- **aapt2 compile: file-by-file, `-o <directory>`** — NOT `--dir`
- **d8.bat broken with JDK 17** — use `java -cp d8.jar com.android.tools.r8.D8`
- **Use apksigner.jar** not jarsigner
- **INSTALL_FAILED_UPDATE_INCOMPATIBLE** — `adb uninstall com.clawphone.weathermarkets`
- **Widget requires Termux monitor running** — if monitor is stopped, widget shows empty

## Polymarket Gamma API Reference

- **Endpoint:** `https://gamma-api.polymarket.com/events`
- **No auth required** — public read-only API
- **Key params:** `closed=false`, `active=true`, `limit=500`, `order=startDate`, `ascending=false`
- **Rate limit:** ~300 req/min (Cloudflare throttling, not hard rejection)
- **DNS note:** Some ISPs resolve Polymarket to 127.0.0.1. On the device, set Private DNS to `dns.google`

## Troubleshooting

- **Widget empty/blank:** Make sure the Termux monitor is running. Check with `curl -s http://127.0.0.1:8788/api`
- **No notifications:** Ensure `termux-api` package is installed AND Termux:API app from F-Droid
- **Monitor shows 0 markets:** Polymarket may not have active weather markets. This is normal — the monitor will catch them when they appear.
- **Too many notifications on start:** Should not happen (first run seeds without notifying). If it does, delete `seen.json` and restart.
- **False positive (sports match):** Add the team name to `SPORTS_EXCLUSIONS` array in monitor.js
- **Polymarket DNS blocked:** Set device Private DNS to `dns.google` in Android Settings > Network
- **Monitor dies:** Check `~/.clawphone/skills/weather-markets/monitor.log`. Restart with the deploy script.

## Extending

- **Add more keyword categories:** Earthquake, volcanic eruption, tsunami, aurora, etc.
- **Price alerts:** Notify when a weather market crosses a threshold (e.g., hurricane > 70% Yes)
- **Tap to open:** Add PendingIntent to open market on polymarket.com in browser
- **Historical tracking:** Log market prices over time in a JSON file
- **Multiple categories:** Support crypto, politics, or other topic filters with the same infrastructure
