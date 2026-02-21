---
name: ont-wallet-widget
description: Native Android home screen widget that shows Ontology (ONT) and ONG token balances with USD values. Fetches balances from the Ontology explorer API and prices from CoinGecko. No server required — the widget fetches data directly. Built for the ClawPhone Android emulator. Use when user asks for ONT balance, Ontology wallet, ONG balance, or ONT widget.
emoji: 🔷
requires:
  bins: []
tags:
  - crypto
  - ontology
  - widget
  - android
---

# Ontology Wallet Widget

A native Android home screen widget that displays ONT and ONG balances with real-time USD prices. Unlike the crypto wallet widget, this is a standalone APK — no Termux server needed. The widget fetches directly from public APIs.

## What This Skill Does

1. Builds a native Android widget APK (~10KB) showing ONT and ONG balances
2. Fetches wallet balances from the Ontology Explorer API (`explorer.ont.io`)
3. Fetches USD prices from CoinGecko (ontology + ong)
4. Displays on the Android home screen with auto-refresh every 30 minutes
5. Shows abbreviated wallet address at the bottom

## Requirements

- **Android SDK** with `build-tools/33.0.2` and `platforms/android-33`
- **JDK 17** (for javac and d8)
- **ADB** access to the device/emulator
- No Termux, no Node.js, no npm — pure native widget

Typical paths (adjust to your setup):
```
SDK:         C:\Users\<USER>\Android\Sdk
Build tools: C:\Users\<USER>\Android\Sdk\build-tools\33.0.2
JDK:         C:\Users\<USER>\Android\jdk17\jdk-17.0.2
Platform:    C:\Users\<USER>\Android\Sdk\platforms\android-33\android.jar
```

## Architecture

```
ONT Widget (APK)
  ├── OntWidgetProvider.java  — BroadcastReceiver that fetches data on update/refresh
  ├── explorer.ont.io API     — Balance lookup by address (no API key)
  ├── CoinGecko API           — USD prices for ONT and ONG
  └── Home screen layout      — Shows ONT/ONG rows with balance + USD value
```

The widget runs entirely inside the APK process — no local server, no Termux dependency. It makes HTTPS requests directly from the widget's background thread.

## Project Structure

All source files live at `/tmp/ont-widget/` on WSL:

```
/tmp/ont-widget/
├── AndroidManifest.xml
├── java/com/clawphone/ontology/OntWidgetProvider.java
├── res/
│   ├── layout/widget_layout.xml
│   ├── values/strings.xml
│   └── xml/ont_widget_info.xml
└── rebuild.ps1
```

## Step 1: Create the project directory

```bash
mkdir -p /tmp/ont-widget/java/com/clawphone/ontology
mkdir -p /tmp/ont-widget/res/{layout,values,xml}
```

## Step 2: AndroidManifest.xml

```xml
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.clawphone.ontology"
    android:versionCode="1"
    android:versionName="1.0">

    <uses-permission android:name="android.permission.INTERNET" />
    <uses-sdk android:minSdkVersion="26" android:targetSdkVersion="33" />

    <application android:label="ONT Wallet">

        <receiver android:name=".OntWidgetProvider"
            android:exported="true">
            <intent-filter>
                <action android:name="android.appwidget.action.APPWIDGET_UPDATE" />
                <action android:name="com.clawphone.ontology.REFRESH" />
            </intent-filter>
            <meta-data
                android:name="android.appwidget.provider"
                android:resource="@xml/ont_widget_info" />
        </receiver>

    </application>
</manifest>
```

Key points:
- `INTERNET` permission required for API calls
- Custom `REFRESH` action allows manual refresh via ADB broadcast
- No `networkSecurityConfig` needed — all API calls are HTTPS (not cleartext localhost)

## Step 3: Widget info (res/xml/ont_widget_info.xml)

```xml
<?xml version="1.0" encoding="utf-8"?>
<appwidget-provider xmlns:android="http://schemas.android.com/apk/res/android"
    android:minWidth="250dp"
    android:minHeight="110dp"
    android:updatePeriodMillis="1800000"
    android:initialLayout="@layout/widget_layout"
    android:resizeMode="horizontal|vertical"
    android:widgetCategory="home_screen" />
```

- `updatePeriodMillis=1800000` = 30 minute auto-refresh (minimum enforced by Android is 30 min)
- `minWidth=250dp` / `minHeight=110dp` = roughly 4x2 cells

## Step 4: Layout (res/layout/widget_layout.xml)

```xml
<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:id="@+id/widget_root"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:orientation="vertical"
    android:background="#FF111111"
    android:padding="12dp">

    <TextView
        android:id="@+id/widget_title"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:text="Ontology Wallet"
        android:textColor="#FF00d4aa"
        android:textSize="16sp"
        android:textStyle="bold"
        android:gravity="center"
        android:paddingBottom="8dp" />

    <LinearLayout
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:orientation="horizontal"
        android:background="#FF1a1a2e"
        android:padding="10dp"
        android:gravity="center_vertical">

        <TextView
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:text="ONT"
            android:textColor="#FF00d4aa"
            android:textSize="16sp"
            android:textStyle="bold"
            android:layout_marginEnd="12dp" />

        <TextView
            android:id="@+id/ont_balance"
            android:layout_width="0dp"
            android:layout_height="wrap_content"
            android:layout_weight="1"
            android:text="--"
            android:textColor="#FFeeeeee"
            android:textSize="20sp"
            android:textStyle="bold" />

        <TextView
            android:id="@+id/ont_usd"
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:text="$--"
            android:textColor="#FF888888"
            android:textSize="14sp" />

    </LinearLayout>

    <TextView
        android:layout_width="match_parent"
        android:layout_height="4dp"
        android:text="" />

    <LinearLayout
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:orientation="horizontal"
        android:background="#FF1a1a2e"
        android:padding="10dp"
        android:gravity="center_vertical">

        <TextView
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:text="ONG"
            android:textColor="#FFffa726"
            android:textSize="16sp"
            android:textStyle="bold"
            android:layout_marginEnd="12dp" />

        <TextView
            android:id="@+id/ong_balance"
            android:layout_width="0dp"
            android:layout_height="wrap_content"
            android:layout_weight="1"
            android:text="--"
            android:textColor="#FFeeeeee"
            android:textSize="20sp"
            android:textStyle="bold" />

        <TextView
            android:id="@+id/ong_usd"
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:text="$--"
            android:textColor="#FF888888"
            android:textSize="14sp" />

    </LinearLayout>

    <TextView
        android:id="@+id/wallet_addr"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:text="Addr...Here"
        android:textColor="#FF555555"
        android:textSize="10sp"
        android:gravity="center"
        android:paddingTop="6dp" />

</LinearLayout>
```

Design notes:
- Dark background (`#111111`) with teal ONT label (`#00d4aa`) and orange ONG label (`#ffa726`)
- Two rows: ONT balance + USD, ONG balance + USD
- Abbreviated wallet address at the bottom
- Dark card backgrounds (`#1a1a2e`) for the balance rows

## Step 5: Strings (res/values/strings.xml)

```xml
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">ONT Wallet</string>
</resources>
```

## Step 6: Java — OntWidgetProvider.java

Create at `java/com/clawphone/ontology/OntWidgetProvider.java`:

```java
package com.clawphone.ontology;

import android.appwidget.AppWidgetManager;
import android.appwidget.AppWidgetProvider;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.util.Log;
import android.widget.RemoteViews;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;

import org.json.JSONArray;
import org.json.JSONObject;

public class OntWidgetProvider extends AppWidgetProvider {

    private static final String TAG = "OntWidget";
    private static final String WALLET = "YOUR_ONT_ADDRESS_HERE";
    private static final String BALANCE_URL = "https://explorer.ont.io/v2/addresses/" + WALLET + "/native/balances";
    private static final String PRICE_URL = "https://api.coingecko.com/api/v3/simple/price?ids=ontology,ong&vs_currencies=usd";

    @Override
    public void onUpdate(Context context, AppWidgetManager appWidgetManager, int[] appWidgetIds) {
        Log.d(TAG, "onUpdate called, ids=" + appWidgetIds.length);
        for (int id : appWidgetIds) {
            updateWidget(context, appWidgetManager, id);
        }
    }

    @Override
    public void onReceive(Context context, Intent intent) {
        super.onReceive(context, intent);
        Log.d(TAG, "onReceive: " + intent.getAction());
        if ("com.clawphone.ontology.REFRESH".equals(intent.getAction())) {
            AppWidgetManager mgr = AppWidgetManager.getInstance(context);
            int[] ids = mgr.getAppWidgetIds(new ComponentName(context, OntWidgetProvider.class));
            Log.d(TAG, "REFRESH: found " + ids.length + " widgets");
            for (int id : ids) {
                updateWidget(context, mgr, id);
            }
        }
    }

    private void updateWidget(final Context context, final AppWidgetManager mgr, final int widgetId) {
        Log.d(TAG, "updateWidget id=" + widgetId);
        new Thread(new Runnable() {
            @Override
            public void run() {
                RemoteViews views = new RemoteViews(context.getPackageName(), R.layout.widget_layout);

                double ontBal = 0, ongBal = 0;
                double ontPrice = 0, ongPrice = 0;

                // Fetch balances from Ontology Explorer
                try {
                    Log.d(TAG, "Fetching balances from: " + BALANCE_URL);
                    String json = httpGet(BALANCE_URL);
                    Log.d(TAG, "Balance response: " + json.substring(0, Math.min(200, json.length())));
                    JSONObject resp = new JSONObject(json);
                    JSONArray result = resp.getJSONArray("result");
                    for (int i = 0; i < result.length(); i++) {
                        JSONObject item = result.getJSONObject(i);
                        String name = item.getString("asset_name");
                        if ("ont".equals(name)) {
                            ontBal = Double.parseDouble(item.getString("balance"));
                        } else if ("ong".equals(name)) {
                            ongBal = Double.parseDouble(item.getString("balance"));
                        }
                    }
                    Log.d(TAG, "Balances: ONT=" + ontBal + " ONG=" + ongBal);
                } catch (Exception e) {
                    Log.e(TAG, "Balance fetch error: " + e.getMessage(), e);
                }

                // Fetch prices from CoinGecko
                try {
                    Log.d(TAG, "Fetching prices...");
                    String json = httpGet(PRICE_URL);
                    Log.d(TAG, "Price response: " + json);
                    JSONObject resp = new JSONObject(json);
                    ontPrice = resp.optJSONObject("ontology") != null ? resp.getJSONObject("ontology").optDouble("usd", 0) : 0;
                    ongPrice = resp.optJSONObject("ong") != null ? resp.getJSONObject("ong").optDouble("usd", 0) : 0;
                    Log.d(TAG, "Prices: ONT=$" + ontPrice + " ONG=$" + ongPrice);
                } catch (Exception e) {
                    Log.e(TAG, "Price fetch error: " + e.getMessage(), e);
                }

                double ontUsd = ontBal * ontPrice;
                double ongUsd = ongBal * ongPrice;

                // Format balances — whole numbers get no decimals, fractional get 2-4
                String ontBalStr = ontBal == (long) ontBal ? String.format("%,d", (long) ontBal) : String.format("%,.2f", ontBal);
                String ongBalStr = ongBal == (long) ongBal ? String.format("%,d", (long) ongBal) : String.format("%,.4f", ongBal);

                Log.d(TAG, "Setting views: ONT=" + ontBalStr + " ONG=" + ongBalStr);
                views.setTextViewText(R.id.ont_balance, ontBalStr);
                views.setTextViewText(R.id.ong_balance, ongBalStr);
                views.setTextViewText(R.id.ont_usd, String.format("$%,.2f", ontUsd));
                views.setTextViewText(R.id.ong_usd, String.format("$%,.2f", ongUsd));
                views.setTextViewText(R.id.wallet_addr, WALLET.substring(0, 6) + "..." + WALLET.substring(WALLET.length() - 4));

                mgr.updateAppWidget(widgetId, views);
                Log.d(TAG, "Widget updated successfully");
            }
        }).start();
    }

    private String httpGet(String urlStr) throws Exception {
        URL url = new URL(urlStr);
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        conn.setConnectTimeout(10000);
        conn.setReadTimeout(10000);
        conn.setRequestProperty("User-Agent", "ClawPhone/1.0");
        int code = conn.getResponseCode();
        Log.d(TAG, "HTTP " + code + " from " + urlStr);
        BufferedReader reader = new BufferedReader(new InputStreamReader(conn.getInputStream()));
        StringBuilder sb = new StringBuilder();
        String line;
        while ((line = reader.readLine()) != null) sb.append(line);
        reader.close();
        conn.disconnect();
        return sb.toString();
    }
}
```

### Configuring the wallet address

The user MUST provide their Ontology wallet address. Ask them:
- "What is your Ontology (ONT) wallet address?"

Then update the `WALLET` constant in `OntWidgetProvider.java`:
```java
private static final String WALLET = "YOUR_ONT_ADDRESS_HERE";
```

### How it works

1. **Balance fetch**: Calls `explorer.ont.io/v2/addresses/{addr}/native/balances` — returns JSON array with `ont`, `ong`, `waitboundong`, `unboundong` entries
2. **Price fetch**: Calls CoinGecko for `ontology` and `ong` USD prices
3. **Display**: Multiplies balance × price for USD values, formats and updates RemoteViews
4. **Refresh**: Auto-updates every 30 minutes via `updatePeriodMillis`, or manually via broadcast

### API Details

**Ontology Explorer API** (no key required):
```
GET https://explorer.ont.io/v2/addresses/{address}/native/balances
```
Response:
```json
{
  "code": 0,
  "msg": "SUCCESS",
  "result": [
    {"balance": "1000", "asset_name": "ont", "asset_type": "native", "contract_hash": "0100..."},
    {"balance": "5.5", "asset_name": "ong", "asset_type": "native", "contract_hash": "0200..."},
    {"balance": "0.3", "asset_name": "waitboundong", ...},
    {"balance": "1.2", "asset_name": "unboundong", ...}
  ]
}
```

**CoinGecko API** (free, no key):
```
GET https://api.coingecko.com/api/v3/simple/price?ids=ontology,ong&vs_currencies=usd
```
Response:
```json
{"ontology": {"usd": 0.1823}, "ong": {"usd": 0.2651}}
```

## Step 7: Build script (rebuild.ps1)

PowerShell build script — runs on the Windows side:

```powershell
$ErrorActionPreference = "Stop"

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

$WORK = "C:\ont-build"
$SRC = "\\wsl.localhost\Ubuntu\tmp\ont-widget"

Write-Host "=== ONT Wallet Widget Build ===" -ForegroundColor Cyan

if (Test-Path $WORK) { Remove-Item -Recurse -Force $WORK }
New-Item -ItemType Directory -Path $WORK -Force | Out-Null
Copy-Item -Recurse "$SRC\*" $WORK

$COMPILED = "$WORK\compiled"
$GEN = "$WORK\gen"
New-Item -ItemType Directory -Path $COMPILED -Force | Out-Null
New-Item -ItemType Directory -Path $GEN -Force | Out-Null

Write-Host "Compiling resources..." -ForegroundColor Yellow
$resFiles = Get-ChildItem -Recurse "$WORK\res" -File
foreach ($f in $resFiles) {
    & $AAPT2 compile $f.FullName -o $COMPILED
    if ($LASTEXITCODE -ne 0) { throw "aapt2 compile failed for $($f.Name)" }
}

Write-Host "Linking resources..." -ForegroundColor Yellow
$flatFiles = Get-ChildItem "$COMPILED\*.flat" | ForEach-Object { $_.FullName }
$linkArgs = @("link", "--auto-add-overlay", "-I", $PLATFORM, "--manifest", "$WORK\AndroidManifest.xml",
    "--java", $GEN, "-o", "$WORK\res.apk")
$linkArgs += $flatFiles
& $AAPT2 @linkArgs
if ($LASTEXITCODE -ne 0) { throw "aapt2 link failed" }

Write-Host "Compiling Java..." -ForegroundColor Yellow
$javaFiles = @(Get-ChildItem -Recurse "$WORK\java\*.java" | ForEach-Object { $_.FullName })
$genJava = @()
if (Test-Path "$GEN") {
    $genJava = @(Get-ChildItem -Recurse "$GEN\*.java" -ErrorAction SilentlyContinue | ForEach-Object { $_.FullName })
}
$allJava = $javaFiles + $genJava
$classesDir = "$WORK\classes"
New-Item -ItemType Directory -Path $classesDir -Force | Out-Null
& $JAVAC -source 11 -target 11 -classpath "$PLATFORM" -d $classesDir @allJava
if ($LASTEXITCODE -ne 0) { throw "javac failed" }

Write-Host "Dexing..." -ForegroundColor Yellow
$classFiles = Get-ChildItem -Recurse "$classesDir\*.class" | ForEach-Object { $_.FullName }
& $JAVA -cp $D8_JAR com.android.tools.r8.D8 --release --output $WORK --lib $PLATFORM @classFiles
if ($LASTEXITCODE -ne 0) { throw "d8 failed" }

Write-Host "Packaging APK..." -ForegroundColor Yellow
Copy-Item "$WORK\res.apk" "$WORK\ont.unsigned.apk"
$AAPT1 = "$BT\aapt.exe"
Push-Location $WORK
& $AAPT1 add ont.unsigned.apk classes.dex
Pop-Location
if ($LASTEXITCODE -ne 0) { throw "aapt add failed" }

Write-Host "Zipaligning..." -ForegroundColor Yellow
& $ZIPALIGN -f 4 "$WORK\ont.unsigned.apk" "$WORK\ont.aligned.apk"
if ($LASTEXITCODE -ne 0) { throw "zipalign failed" }

Write-Host "Signing..." -ForegroundColor Yellow
$KS = "$WORK\debug.keystore"
if (-not (Test-Path $KS)) {
    & "$JDK\bin\keytool.exe" -genkeypair -v -keystore $KS -storepass android -keypass android -keyalg RSA -keysize 2048 -validity 10000 -alias androiddebugkey -dname "CN=Debug,O=Android,C=US"
}
& $JAVA -jar $APKSIGNER_JAR sign --ks $KS --ks-pass pass:android --key-pass pass:android --out "$WORK\ont.apk" "$WORK\ont.aligned.apk"
if ($LASTEXITCODE -ne 0) { throw "apksigner failed" }

Write-Host "Installing..." -ForegroundColor Green
& $ADB install -r "$WORK\ont.apk"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Install failed - trying uninstall first..." -ForegroundColor Yellow
    & $ADB uninstall com.clawphone.ontology
    & $ADB install "$WORK\ont.apk"
}

Write-Host "=== BUILD SUCCESS ===" -ForegroundColor Green
```

Run with:
```
powershell.exe -ExecutionPolicy Bypass -File '\\wsl.localhost\Ubuntu\tmp\ont-widget\rebuild.ps1'
```

## Step 8: Add widget to home screen

After installing, add the widget:

1. Long-press on an empty area of the home screen
2. Tap "Widgets"
3. Scroll to find "ONT Wallet"
4. Tap to expand, long-press and drag the widget preview onto the home screen

**Via ADB (UI automation):**
```bash
ADB="/mnt/c/Users/Clawdbotdave/Android/Sdk/platform-tools/adb.exe"
# Long press home screen
$ADB shell input swipe 540 1200 540 1200 1500
# Use tap.sh helper
$ADB shell "sh /data/local/tmp/tap.sh 'Widgets'"
# Scroll to ONT Wallet, then drag to place
```

## Manual Refresh

Trigger a widget refresh via ADB:
```bash
adb shell "am broadcast -a com.clawphone.ontology.REFRESH -n com.clawphone.ontology/.OntWidgetProvider"
```

## Build Gotchas

Same as the crypto wallet widget build — see the crypto-wallet-widget.md for full details:

- **UNC paths break aapt2/d8** — the build script copies to `C:\ont-build` first
- **aapt2 compile: file-by-file with `-o <directory>`** — NOT `--dir` (silently fails)
- **d8.bat broken with JDK 17** — use `java -cp d8.jar com.android.tools.r8.D8` directly
- **Use apksigner.jar** not jarsigner (Android 13+ needs v2+ signatures)
- **INSTALL_FAILED_UPDATE_INCOMPATIBLE** — run `adb uninstall com.clawphone.ontology` when keystore changes

## Differences from Crypto Wallet Widget

| Feature | Crypto Wallet Widget | ONT Widget |
|---------|---------------------|------------|
| Server needed | Yes (Node.js in Termux) | No (standalone) |
| Data source | localhost:8787 API | Direct HTTPS to explorer.ont.io |
| Chains | ETH, SOL | ONT, ONG |
| Network config | Needs cleartext for localhost | HTTPS only, no special config |
| Refresh | 5 min (server-side) | 30 min (Android minimum) |
| Dependencies | Node.js 18+ | None |

## Known Issues & Fixes

- **Widget shows 0/0**: Verify the wallet address has ONT/ONG. Check with: `curl -s "https://explorer.ont.io/v2/addresses/YOUR_ADDRESS/native/balances"`
- **Widget shows "--"**: First update hasn't fired yet. Send a manual REFRESH broadcast.
- **CoinGecko rate limit**: Prices show $0. Wait a few minutes. CoinGecko free tier allows ~30 calls/min.
- **INSTALL_FAILED_UPDATE_INCOMPATIBLE**: `adb uninstall com.clawphone.ontology` then reinstall.
- **No logcat output**: Check `adb logcat -s OntWidget:*` — if empty, the widget process may not be running. Send a REFRESH broadcast to trigger it.
- **Ontology Explorer API down**: The widget will show stale data. The explorer API has occasional downtime.

## Extending This Skill

- **Add OEP-4 tokens**: Fetch token balances via `explorer.ont.io/v2/addresses/{addr}/oep4/balances`
- **Add staking info**: Show staked ONT and pending ONG rewards
- **Price change indicator**: Add 24h change from CoinGecko (add `&include_24hr_change=true` to price URL)
- **Multiple wallets**: Support an array of addresses and sum the balances
- **Tap to open**: Add PendingIntent to open Ontology explorer in browser on tap
