---
name: polymarket-new-markets
description: Shows the newest Polymarket prediction markets as a native Android home screen widget. Displays the 6 most recently created markets with their current Yes% price. Green for >= 50%, orange for < 50%. Auto-refreshes every 30 minutes. No server needed — fetches directly from Polymarket Gamma API. Use when user wants prediction markets, Polymarket widget, or new markets on home screen.
emoji: 🔮
requires:
  bins: []
tags:
  - polymarket
  - prediction-markets
  - widget
  - android
---

# Polymarket New Markets Widget

A native Android home screen widget that shows the newest prediction markets from Polymarket in real-time. No Termux server required — the widget fetches directly from the Polymarket Gamma API over HTTPS.

## What This Widget Shows

- The 6 most recently created markets on Polymarket
- Each market's question and current Yes% price
- Green percentage = 50% or higher, orange = below 50%
- Auto-refreshes every 30 minutes

## Requirements

- Android SDK build-tools 33+, JDK 17 (on Windows side)
- Internet connection on the device
- No npm dependencies, no server, no Termux needed

## DNS Note

If Polymarket domains resolve to `127.0.0.1` (some ISPs/DNS providers block it), fix it on the Android device:
- Settings > Network > Private DNS > set to `dns.google`

## Setup Instructions

### Step 1: Create the project directory

```bash
mkdir -p /tmp/polymarket-widget/java/com/clawphone/polymarket
mkdir -p /tmp/polymarket-widget/res/layout
mkdir -p /tmp/polymarket-widget/res/xml
mkdir -p /tmp/polymarket-widget/res/values
```

### Step 2: Create AndroidManifest.xml

Create `/tmp/polymarket-widget/AndroidManifest.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.clawphone.polymarket"
    android:versionCode="1"
    android:versionName="1.0">

    <uses-permission android:name="android.permission.INTERNET" />
    <uses-sdk android:minSdkVersion="26" android:targetSdkVersion="33" />

    <application android:label="Polymarket">

        <receiver android:name=".PolymarketWidgetProvider"
            android:exported="true">
            <intent-filter>
                <action android:name="android.appwidget.action.APPWIDGET_UPDATE" />
                <action android:name="com.clawphone.polymarket.REFRESH" />
            </intent-filter>
            <meta-data
                android:name="android.appwidget.provider"
                android:resource="@xml/polymarket_widget_info" />
        </receiver>

        <service android:name=".PolymarketWidgetService"
            android:permission="android.permission.BIND_REMOTEVIEWS"
            android:exported="false" />

    </application>
</manifest>
```

### Step 3: Create widget info XML

Create `/tmp/polymarket-widget/res/xml/polymarket_widget_info.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<appwidget-provider xmlns:android="http://schemas.android.com/apk/res/android"
    android:minWidth="250dp"
    android:minHeight="250dp"
    android:updatePeriodMillis="1800000"
    android:initialLayout="@layout/widget_layout"
    android:resizeMode="horizontal|vertical"
    android:widgetCategory="home_screen" />
```

### Step 4: Create layout files

Create `/tmp/polymarket-widget/res/layout/widget_layout.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:id="@+id/widget_root"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:orientation="vertical"
    android:background="#FF111111"
    android:padding="8dp">

    <TextView
        android:id="@+id/widget_title"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:text="Polymarket New Markets"
        android:textColor="#FFa78bfa"
        android:textSize="16sp"
        android:textStyle="bold"
        android:gravity="center"
        android:paddingBottom="4dp" />

    <ListView
        android:id="@+id/market_list"
        android:layout_width="match_parent"
        android:layout_height="match_parent"
        android:divider="@android:color/transparent"
        android:dividerHeight="4dp" />

</LinearLayout>
```

Create `/tmp/polymarket-widget/res/layout/widget_item.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:orientation="horizontal"
    android:background="#FF1a1a2e"
    android:padding="8dp"
    android:gravity="center_vertical">

    <TextView
        android:id="@+id/item_question"
        android:layout_width="0dp"
        android:layout_height="wrap_content"
        android:layout_weight="1"
        android:textColor="#FFeeeeee"
        android:textSize="13sp"
        android:maxLines="2"
        android:ellipsize="end"
        android:paddingEnd="8dp" />

    <TextView
        android:id="@+id/item_pct"
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:textColor="#FF4caf50"
        android:textSize="18sp"
        android:textStyle="bold" />

</LinearLayout>
```

Create `/tmp/polymarket-widget/res/values/strings.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">Polymarket</string>
</resources>
```

### Step 5: Create PolymarketWidgetProvider.java

Create `/tmp/polymarket-widget/java/com/clawphone/polymarket/PolymarketWidgetProvider.java`:

```java
package com.clawphone.polymarket;

import android.appwidget.AppWidgetManager;
import android.appwidget.AppWidgetProvider;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import android.widget.RemoteViews;

public class PolymarketWidgetProvider extends AppWidgetProvider {

    @Override
    public void onUpdate(Context context, AppWidgetManager appWidgetManager, int[] appWidgetIds) {
        for (int appWidgetId : appWidgetIds) {
            updateWidget(context, appWidgetManager, appWidgetId);
        }
    }

    @Override
    public void onReceive(Context context, Intent intent) {
        super.onReceive(context, intent);
        if ("com.clawphone.polymarket.REFRESH".equals(intent.getAction())) {
            AppWidgetManager mgr = AppWidgetManager.getInstance(context);
            int[] ids = mgr.getAppWidgetIds(new ComponentName(context, PolymarketWidgetProvider.class));
            mgr.notifyAppWidgetViewDataChanged(ids, R.id.market_list);
            for (int id : ids) {
                updateWidget(context, mgr, id);
            }
        }
    }

    private void updateWidget(Context context, AppWidgetManager appWidgetManager, int appWidgetId) {
        Intent intent = new Intent(context, PolymarketWidgetService.class);
        intent.putExtra(AppWidgetManager.EXTRA_APPWIDGET_ID, appWidgetId);
        intent.setData(Uri.parse(intent.toUri(Intent.URI_INTENT_SCHEME)));

        RemoteViews views = new RemoteViews(context.getPackageName(), R.layout.widget_layout);
        views.setRemoteAdapter(R.id.market_list, intent);
        views.setEmptyView(R.id.market_list, R.id.widget_title);

        appWidgetManager.updateAppWidget(appWidgetId, views);
        appWidgetManager.notifyAppWidgetViewDataChanged(appWidgetId, R.id.market_list);
    }
}
```

### Step 6: Create PolymarketWidgetService.java

Create `/tmp/polymarket-widget/java/com/clawphone/polymarket/PolymarketWidgetService.java`:

```java
package com.clawphone.polymarket;

import android.content.Context;
import android.content.Intent;
import android.widget.RemoteViews;
import android.widget.RemoteViewsService;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;

import org.json.JSONArray;
import org.json.JSONObject;

public class PolymarketWidgetService extends RemoteViewsService {
    @Override
    public RemoteViewsFactory onGetViewFactory(Intent intent) {
        return new PolymarketFactory(getApplicationContext());
    }

    static class PolymarketFactory implements RemoteViewsFactory {
        private static final String API_URL = "https://gamma-api.polymarket.com/markets?closed=false&limit=6&order=startDate&ascending=false&active=true";

        private Context context;
        private JSONArray markets = new JSONArray();

        PolymarketFactory(Context context) {
            this.context = context;
        }

        @Override
        public void onCreate() {}

        @Override
        public void onDataSetChanged() {
            try {
                URL url = new URL(API_URL);
                HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                conn.setConnectTimeout(10000);
                conn.setReadTimeout(10000);
                conn.setRequestProperty("User-Agent", "ClawPhone/1.0");
                BufferedReader reader = new BufferedReader(new InputStreamReader(conn.getInputStream()));
                StringBuilder sb = new StringBuilder();
                String line;
                while ((line = reader.readLine()) != null) sb.append(line);
                reader.close();
                conn.disconnect();

                JSONArray raw = new JSONArray(sb.toString());
                markets = new JSONArray();
                for (int i = 0; i < raw.length(); i++) {
                    JSONObject m = raw.getJSONObject(i);
                    JSONObject item = new JSONObject();
                    item.put("question", m.optString("question", "Unknown"));

                    double yes = 0;
                    String pricesStr = m.optString("outcomePrices", "");
                    if (pricesStr.length() > 2) {
                        try {
                            JSONArray prices = new JSONArray(pricesStr);
                            yes = prices.getDouble(0);
                        } catch (Exception e) {}
                    }
                    item.put("yes", yes);
                    item.put("volume", m.optDouble("volume24hr", 0));
                    markets.put(item);
                }
            } catch (Exception e) {
                e.printStackTrace();
            }
        }

        @Override
        public void onDestroy() {}

        @Override
        public int getCount() {
            return markets.length();
        }

        @Override
        public RemoteViews getViewAt(int position) {
            RemoteViews views = new RemoteViews(context.getPackageName(), R.layout.widget_item);
            try {
                JSONObject m = markets.getJSONObject(position);
                String question = m.getString("question");
                double yes = m.getDouble("yes");
                int pct = (int) Math.round(yes * 100);
                double vol = m.optDouble("volume", 0);
                String volStr = vol >= 1000 ? String.format("$%.0fk", vol / 1000) : String.format("$%.0f", vol);

                views.setTextViewText(R.id.item_question, question);
                views.setTextViewText(R.id.item_pct, pct + "%");

                if (pct >= 50) {
                    views.setTextColor(R.id.item_pct, 0xFF4CAF50);
                } else {
                    views.setTextColor(R.id.item_pct, 0xFFFF5722);
                }
            } catch (Exception e) {
                views.setTextViewText(R.id.item_question, "Loading...");
                views.setTextViewText(R.id.item_pct, "--");
            }
            return views;
        }

        @Override
        public RemoteViews getLoadingView() { return null; }

        @Override
        public int getViewTypeCount() { return 1; }

        @Override
        public long getItemId(int position) { return position; }

        @Override
        public boolean hasStableIds() { return false; }
    }
}
```

### Step 7: Create the build script

Create `/tmp/polymarket-widget/rebuild.ps1`:

```powershell
$ErrorActionPreference = "Stop"

# Paths
$SDK = "C:\Users\<USER>\Android\Sdk"
$BT = "$SDK\build-tools\33.0.2"
$PLATFORM = "$SDK\platforms\android-33\android.jar"
$JDK = "C:\Users\<USER>\Android\jdk17\jdk-17.0.2"
$JAVAC = "$JDK\bin\javac.exe"
$JAVA = "$JDK\bin\java.exe"
$AAPT2 = "$BT\aapt2.exe"
$ZIPALIGN = "$BT\zipalign.exe"
$D8_JAR = "$BT\lib\d8.jar"
$APKSIGNER_JAR = "$BT\lib\apksigner.jar"
$ADB = "$SDK\platform-tools\adb.exe"

# Work in Windows-local temp to avoid UNC path issues
$WORK = "C:\polymarket-build"
$SRC = "\\wsl.localhost\Ubuntu\tmp\polymarket-widget"

Write-Host "=== Polymarket Widget Build ===" -ForegroundColor Cyan

# Clean and copy source
if (Test-Path $WORK) { Remove-Item -Recurse -Force $WORK }
New-Item -ItemType Directory -Path $WORK -Force | Out-Null
Copy-Item -Recurse "$SRC\*" $WORK

# Create output dirs
$COMPILED = "$WORK\compiled"
$GEN = "$WORK\gen"
New-Item -ItemType Directory -Path $COMPILED -Force | Out-Null
New-Item -ItemType Directory -Path $GEN -Force | Out-Null

# aapt2 compile - file by file
Write-Host "Compiling resources..." -ForegroundColor Yellow
$resFiles = Get-ChildItem -Recurse "$WORK\res" -File
foreach ($f in $resFiles) {
    & $AAPT2 compile $f.FullName -o $COMPILED
    if ($LASTEXITCODE -ne 0) { throw "aapt2 compile failed for $($f.Name)" }
}

# aapt2 link
Write-Host "Linking resources..." -ForegroundColor Yellow
$flatFiles = Get-ChildItem "$COMPILED\*.flat" | ForEach-Object { $_.FullName }
$linkArgs = @("link", "--auto-add-overlay", "-I", $PLATFORM, "--manifest", "$WORK\AndroidManifest.xml",
    "--java", $GEN, "-o", "$WORK\res.apk")
$linkArgs += $flatFiles
& $AAPT2 @linkArgs
if ($LASTEXITCODE -ne 0) { throw "aapt2 link failed" }

# Compile Java
Write-Host "Compiling Java..." -ForegroundColor Yellow
$javaFiles = Get-ChildItem -Recurse "$WORK\java\*.java" | ForEach-Object { $_.FullName }
$genJava = @()
if (Test-Path "$GEN") {
    $genJava = Get-ChildItem -Recurse "$GEN\*.java" -ErrorAction SilentlyContinue | ForEach-Object { $_.FullName }
}
$allJava = $javaFiles + $genJava
$classesDir = "$WORK\classes"
New-Item -ItemType Directory -Path $classesDir -Force | Out-Null
& $JAVAC -source 11 -target 11 -classpath $PLATFORM -d $classesDir @allJava
if ($LASTEXITCODE -ne 0) { throw "javac failed" }

# d8 (dex)
Write-Host "Dexing..." -ForegroundColor Yellow
$classFiles = Get-ChildItem -Recurse "$classesDir\*.class" | ForEach-Object { $_.FullName }
& $JAVA -cp $D8_JAR com.android.tools.r8.D8 --release --output $WORK --lib $PLATFORM @classFiles
if ($LASTEXITCODE -ne 0) { throw "d8 failed" }

# Add classes.dex to APK
Write-Host "Packaging APK..." -ForegroundColor Yellow
Copy-Item "$WORK\res.apk" "$WORK\polymarket.unsigned.apk"

$AAPT1 = "$BT\aapt.exe"
Push-Location $WORK
& $AAPT1 add polymarket.unsigned.apk classes.dex
Pop-Location
if ($LASTEXITCODE -ne 0) { throw "aapt add failed" }

# Zipalign
Write-Host "Zipaligning..." -ForegroundColor Yellow
& $ZIPALIGN -f 4 "$WORK\polymarket.unsigned.apk" "$WORK\polymarket.aligned.apk"
if ($LASTEXITCODE -ne 0) { throw "zipalign failed" }

# Sign
Write-Host "Signing..." -ForegroundColor Yellow
$KS = "$WORK\debug.keystore"
if (-not (Test-Path $KS)) {
    & "$JDK\bin\keytool.exe" -genkeypair -v -keystore $KS -storepass android -keypass android -keyalg RSA -keysize 2048 -validity 10000 -alias androiddebugkey -dname "CN=Debug,O=Android,C=US"
}
& $JAVA -jar $APKSIGNER_JAR sign --ks $KS --ks-pass pass:android --key-pass pass:android --out "$WORK\polymarket.apk" "$WORK\polymarket.aligned.apk"
if ($LASTEXITCODE -ne 0) { throw "apksigner failed" }

# Install
Write-Host "Installing..." -ForegroundColor Green
& $ADB install -r "$WORK\polymarket.apk"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Install failed - trying uninstall first..." -ForegroundColor Yellow
    & $ADB uninstall com.clawphone.polymarket
    & $ADB install "$WORK\polymarket.apk"
}

Write-Host "=== BUILD SUCCESS ===" -ForegroundColor Green
```

### Step 8: Build and install

Run the build from WSL:

```bash
powershell.exe -ExecutionPolicy Bypass -File '\\wsl.localhost\Ubuntu\tmp\polymarket-widget\rebuild.ps1'
```

### Step 9: Add widget to home screen

1. Long-press an empty area on the home screen
2. Tap **Widgets**
3. Search for **Polymarket**
4. Drag the **Polymarket 3x4** widget onto your home screen

### Step 10: Force refresh (optional)

```bash
ADB="/mnt/c/Users/<USER>/Android/Sdk/platform-tools/adb.exe"
$ADB shell "am broadcast -a com.clawphone.polymarket.REFRESH -n com.clawphone.polymarket/.PolymarketWidgetProvider"
```

## Build Gotchas

- **UNC paths break aapt2/d8** — the build script copies source to `C:\polymarket-build` first
- **aapt2 compile** must be file-by-file with `-o <directory>`, NOT `--dir`
- **d8.bat is broken with JDK 17** — use `java -cp d8.jar com.android.tools.r8.D8` directly
- **Use apksigner.jar** not jarsigner (Android 13+ needs v2+ signatures)
- **INSTALL_FAILED_UPDATE_INCOMPATIBLE** — run `adb uninstall com.clawphone.polymarket` when keystore changes
- **DNS blocking** — if Polymarket resolves to 127.0.0.1, set device Private DNS to `dns.google`

## API Details

- **Endpoint:** `https://gamma-api.polymarket.com/markets?closed=false&limit=6&order=startDate&ascending=false&active=true`
- **No auth required** — public read-only API
- Returns JSON array of market objects with `question`, `outcomePrices` (stringified JSON array), `volume24hr`, `startDate`
- `outcomePrices` format: `["0.52","0.48"]` where index 0 = Yes price, index 1 = No price
