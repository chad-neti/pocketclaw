---
name: crypto-wallet-widget
description: Fetches real-time crypto wallet balances (Solana, Ethereum) and serves a live dashboard widget accessible from the Android home screen. Includes native Android widget APK build. Built for Termux on Android. Use when user asks for wallet balances, portfolio dashboard, crypto widget, or home screen portfolio.
emoji: 💰
requires:
  bins:
    - node
tags:
  - crypto
  - dashboard
  - widget
  - termux
  - android
---

# Crypto Wallet Widget

A skill that fetches crypto wallet balances and displays them as a live widget on Android — both as a browser dashboard and as a native home screen widget.

## What This Skill Does

1. Creates a Node.js server that fetches wallet balances from public RPCs (no API key needed)
2. Generates a self-contained HTML dashboard with live prices from CoinGecko
3. Serves it on localhost:8787 with a JSON API endpoint
4. Builds a native Android widget APK that reads from the API and shows the balance directly on the home screen
5. Auto-refreshes every 5 minutes

## Requirements

- **Node.js 18+** (for built-in `fetch` API). Node 25+ recommended and tested.
- Zero npm dependencies - pure Node.js with built-in `http` and `fetch`
- **For native widget (optional):** Android SDK build-tools 33+, JDK 17, available via WSL or host

## Part 1: Server Setup (Termux)

### Step 1: Create the project directory

```bash
mkdir -p ~/.clawphone/skills/crypto-wallet-widget
cd ~/.clawphone/skills/crypto-wallet-widget
```

### Step 2: Create the balance fetcher script

Create a file called `server.js` with the following content. This is the entire backend and frontend in one file.

The user MUST provide their wallet addresses. Ask them:
- "What are your Solana wallet addresses?"
- "What are your Ethereum wallet addresses?"

```javascript
const http = require('http');

// ============ USER CONFIG ============
// Replace these with the user's actual wallet addresses
const WALLETS = {
  solana: [
    // { address: 'USER_SOL_ADDRESS_HERE', label: 'Main' },
  ],
  ethereum: [
    // { address: 'USER_ETH_ADDRESS_HERE', label: 'Main' },
  ]
};

const PORT = 8787;
const REFRESH_SECONDS = 300; // 5 minutes
// =====================================

// NOTE: Uses built-in fetch() (Node 18+). Do NOT use the https module -
// it has DNS/TLS resolution issues inside Termux/Android emulators.

async function getEthBalance(address) {
  try {
    const res = await fetch('https://eth.llamarpc.com', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'eth_getBalance', params: [address, 'latest'] })
    });
    const data = await res.json();
    return parseInt(data.result, 16) / 1e18;
  } catch(e) { console.error('ETH err:', e.message); return 0; }
}

async function getSolBalance(address) {
  try {
    const res = await fetch('https://api.mainnet-beta.solana.com', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'getBalance', params: [address] })
    });
    const data = await res.json();
    return (data.result?.value || 0) / 1e9;
  } catch(e) { console.error('SOL err:', e.message); return 0; }
}

async function getPrices() {
  try {
    const res = await fetch('https://api.coingecko.com/api/v3/simple/price?ids=solana,ethereum&vs_currencies=usd&include_24hr_change=true');
    return await res.json();
  } catch(e) {
    console.error('Price err:', e.message);
    return { solana: { usd: 0, usd_24h_change: 0 }, ethereum: { usd: 0, usd_24h_change: 0 } };
  }
}

async function fetchAll() {
  const prices = await getPrices();
  const solPrice = prices.solana?.usd || 0;
  const ethPrice = prices.ethereum?.usd || 0;
  const solChange = prices.solana?.usd_24h_change || 0;
  const ethChange = prices.ethereum?.usd_24h_change || 0;
  const balances = { solana: [], ethereum: [], totalUsd: 0 };

  for (const w of WALLETS.solana) {
    const bal = await getSolBalance(w.address);
    const usd = bal * solPrice;
    balances.solana.push({ ...w, balance: bal, usd });
    balances.totalUsd += usd;
  }
  for (const w of WALLETS.ethereum) {
    const bal = await getEthBalance(w.address);
    const usd = bal * ethPrice;
    balances.ethereum.push({ ...w, balance: bal, usd });
    balances.totalUsd += usd;
  }

  return { balances, prices: { SOL: { price: solPrice, change: solChange }, ETH: { price: ethPrice, change: ethChange } }, updated: new Date().toLocaleTimeString() };
}

function renderHTML(data) {
  const fmt = (n) => n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  const color = (v) => v >= 0 ? '#4ade80' : '#f87171';
  const arrow = (v) => v >= 0 ? '▲' : '▼';
  let rows = '';
  for (const w of data.balances.solana) rows += '<div class="row"><span class="label">◎ '+w.label+'</span><span class="val">'+fmt(w.balance)+' SOL</span><span class="usd">$'+fmt(w.usd)+'</span></div>';
  for (const w of data.balances.ethereum) rows += '<div class="row"><span class="label">Ξ '+w.label+'</span><span class="val">'+fmt(w.balance)+' ETH</span><span class="usd">$'+fmt(w.usd)+'</span></div>';

  return `<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="refresh" content="${REFRESH_SECONDS}"><title>Wallet</title>
<style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:-apple-system,system-ui,sans-serif;background:#0a0a0a;color:#e5e5e5;padding:16px;min-height:100vh}.total{font-size:2.2em;font-weight:700;text-align:center;padding:16px 0 8px;color:#fff}.prices{display:flex;justify-content:center;gap:20px;padding:8px 0 20px;font-size:0.85em}.price-tag{opacity:0.7}.change{font-weight:600}.divider{border:none;border-top:1px solid #222;margin:8px 0}.row{display:flex;justify-content:space-between;align-items:center;padding:12px 4px;border-bottom:1px solid #1a1a1a}.label{flex:1;font-weight:500}.val{flex:1;text-align:right;opacity:0.7;font-size:0.9em}.usd{flex:0.7;text-align:right;font-weight:600}.footer{text-align:center;padding:16px;font-size:0.75em;opacity:0.4}</style></head><body>
<div class="total">$\${fmt(data.balances.totalUsd)}</div>
<div class="prices"><span><span class="price-tag">SOL $\${fmt(data.prices.SOL.price)}</span> <span class="change" style="color:\${color(data.prices.SOL.change)}">\${arrow(data.prices.SOL.change)}\${Math.abs(data.prices.SOL.change).toFixed(1)}%</span></span><span><span class="price-tag">ETH $\${fmt(data.prices.ETH.price)}</span> <span class="change" style="color:\${color(data.prices.ETH.change)}">\${arrow(data.prices.ETH.change)}\${Math.abs(data.prices.ETH.change).toFixed(1)}%</span></span></div>
<hr class="divider">\${rows}
<div class="footer">Updated \${data.updated} · auto-refresh \${REFRESH_SECONDS}s</div></body></html>`;
}

const server = http.createServer(async (req, res) => {
  const data = await fetchAll();
  if (req.url === '/api') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify(data));
  } else {
    res.writeHead(200, { 'Content-Type': 'text/html' });
    res.end(renderHTML(data));
  }
});

// IMPORTANT: Bind to '0.0.0.0' (IPv4) explicitly. Node.js defaults to '::' (IPv6 only),
// which the Android widget's HttpURLConnection cannot reach via 127.0.0.1.
server.listen(PORT, '0.0.0.0', () => console.log('Wallet widget running at http://localhost:' + PORT));
```

### Step 3: Configure wallet addresses

After creating the file, ask the user for their wallet addresses and update the WALLETS object in server.js. Replace the commented placeholder lines.

Example:
```javascript
const WALLETS = {
  solana: [
    { address: '7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU', label: 'Main' },
  ],
  ethereum: [
    { address: '0x742d35Cc6634C0532925a3b844Bc9e7595f2bD18', label: 'Main' },
  ]
};
```

### Step 4: Install and run

```bash
# No npm install needed - zero dependencies, pure Node.js
# Requires Node.js 18+ for built-in fetch(). Install with: pkg install nodejs

# Test it
node ~/.clawphone/skills/crypto-wallet-widget/server.js &

# Verify it works
sleep 2 && curl -s http://localhost:8787/api | head -c 200
```

### Step 5: Make it persistent (Termux)

```bash
mkdir -p ~/.termux/boot
cat > ~/.termux/boot/crypto-widget.sh << 'EOF'
#!/data/data/com.termux/files/usr/bin/sh
termux-wake-lock
node ~/.clawphone/skills/crypto-wallet-widget/server.js &
EOF
chmod +x ~/.termux/boot/crypto-widget.sh
```

This requires the **Termux:Boot** add-on from F-Droid.

## Part 2: Native Android Home Screen Widget

This builds a native Android widget APK (~10KB) that displays the wallet balance directly on the home screen without opening a browser. It fetches from the server.js API running in Termux.

### Prerequisites

These must be available on the Windows/host side (not inside the emulator):
- **Android SDK** with `build-tools/33.0.2` and `platforms/android-33`
- **JDK 17** (for javac and d8)
- **ADB** access to the device/emulator

Typical paths (adjust to your setup):
```
SDK:         C:\Users\<USER>\Android\Sdk
Build tools: C:\Users\<USER>\Android\Sdk\build-tools\33.0.2
JDK:         C:\Users\<USER>\Android\jdk17\jdk-17.0.2
Platform:    C:\Users\<USER>\Android\Sdk\platforms\android-33\android.jar
```

If build-tools are missing: `sdkmanager "build-tools;33.0.2"`

### Step 6: Create the widget project

Create the following files in a project directory (e.g. `/tmp/wallet-widget/`):

#### AndroidManifest.xml

```xml
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.clawphone.wallet"
    android:versionCode="1"
    android:versionName="1.0">

    <uses-sdk android:minSdkVersion="26" android:targetSdkVersion="33" />
    <uses-permission android:name="android.permission.INTERNET" />

    <application
        android:label="Wallet Widget"
        android:icon="@drawable/ic_wallet"
        android:networkSecurityConfig="@xml/network_security_config"
        android:usesCleartextTraffic="true">

        <receiver
            android:name=".WalletWidgetProvider"
            android:exported="true">
            <intent-filter>
                <action android:name="android.appwidget.action.APPWIDGET_UPDATE" />
            </intent-filter>
            <meta-data
                android:name="android.appwidget.provider"
                android:resource="@xml/wallet_widget_info" />
        </receiver>

    </application>
</manifest>
```

#### res/xml/wallet_widget_info.xml

```xml
<?xml version="1.0" encoding="utf-8"?>
<appwidget-provider xmlns:android="http://schemas.android.com/apk/res/android"
    android:minWidth="180dp"
    android:minHeight="40dp"
    android:updatePeriodMillis="300000"
    android:initialLayout="@layout/widget_layout"
    android:resizeMode="horizontal|vertical"
    android:widgetCategory="home_screen"
    android:description="@string/widget_desc" />
```

#### res/xml/network_security_config.xml

**Critical:** Android 9+ blocks cleartext HTTP by default. This allows it for localhost.

```xml
<?xml version="1.0" encoding="utf-8"?>
<network-security-config>
    <domain-config cleartextTrafficPermitted="true">
        <domain includeSubdomains="true">localhost</domain>
        <domain includeSubdomains="true">127.0.0.1</domain>
    </domain-config>
</network-security-config>
```

#### res/layout/widget_layout.xml

```xml
<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:orientation="vertical"
    android:gravity="center"
    android:padding="8dp"
    android:background="#CC0A0A0A"
    android:id="@+id/widget_root">

    <TextView
        android:id="@+id/total_usd"
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:text="$---.--"
        android:textSize="28sp"
        android:textColor="#FFFFFF"
        android:textStyle="bold"
        android:fontFamily="sans-serif-medium" />

    <LinearLayout
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:orientation="horizontal"
        android:gravity="center"
        android:layout_marginTop="2dp">

        <TextView
            android:id="@+id/eth_price"
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:text="ETH $---"
            android:textSize="12sp"
            android:textColor="#AAAAAA" />

        <TextView
            android:id="@+id/eth_change"
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:text=""
            android:textSize="12sp"
            android:textColor="#4ADE80"
            android:layout_marginStart="6dp" />

    </LinearLayout>

    <TextView
        android:id="@+id/updated_at"
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:text="Updating..."
        android:textSize="9sp"
        android:textColor="#555555"
        android:layout_marginTop="2dp" />

</LinearLayout>
```

#### res/values/strings.xml

```xml
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">Wallet Widget</string>
    <string name="widget_desc">Shows crypto wallet balance</string>
</resources>
```

#### res/drawable/ic_wallet.xml

```xml
<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android"
    android:shape="oval">
    <solid android:color="#4ADE80" />
    <size android:width="48dp" android:height="48dp" />
</shape>
```

#### src/com/clawphone/wallet/WalletWidgetProvider.java

```java
package com.clawphone.wallet;

import android.app.PendingIntent;
import android.appwidget.AppWidgetManager;
import android.appwidget.AppWidgetProvider;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import android.widget.RemoteViews;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import android.util.Log;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

public class WalletWidgetProvider extends AppWidgetProvider {

    private static final String ACTION_REFRESH = "com.clawphone.wallet.REFRESH";

    @Override
    public void onUpdate(Context context, AppWidgetManager appWidgetManager, int[] appWidgetIds) {
        for (int appWidgetId : appWidgetIds) {
            updateWidget(context, appWidgetManager, appWidgetId);
        }
    }

    @Override
    public void onReceive(Context context, Intent intent) {
        super.onReceive(context, intent);
        if (ACTION_REFRESH.equals(intent.getAction())) {
            AppWidgetManager mgr = AppWidgetManager.getInstance(context);
            ComponentName cn = new ComponentName(context, WalletWidgetProvider.class);
            int[] ids = mgr.getAppWidgetIds(cn);
            onUpdate(context, mgr, ids);
        }
    }

    static void updateWidget(Context context, AppWidgetManager appWidgetManager, int appWidgetId) {
        RemoteViews views = new RemoteViews(context.getPackageName(), R.layout.widget_layout);

        // Tap widget to open full dashboard in Chrome
        Intent browserIntent = new Intent(Intent.ACTION_VIEW, Uri.parse("http://localhost:8787"));
        PendingIntent pendingBrowser = PendingIntent.getActivity(context, 0, browserIntent, PendingIntent.FLAG_IMMUTABLE);
        views.setOnClickPendingIntent(R.id.widget_root, pendingBrowser);
        appWidgetManager.updateAppWidget(appWidgetId, views);

        // Fetch data in background thread
        final int widgetId = appWidgetId;
        new Thread(() -> {
            try {
                // IMPORTANT: Use 127.0.0.1, NOT localhost. On Android, "localhost"
                // may not resolve correctly from widget processes.
                URL url = new URL("http://127.0.0.1:8787/api");
                HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                conn.setConnectTimeout(5000);
                conn.setReadTimeout(5000);
                BufferedReader reader = new BufferedReader(new InputStreamReader(conn.getInputStream()));
                StringBuilder sb = new StringBuilder();
                String line;
                while ((line = reader.readLine()) != null) sb.append(line);
                reader.close();
                conn.disconnect();

                String json = sb.toString();

                // Simple JSON parsing (no library dependencies)
                double totalUsd = parseDouble(json, "totalUsd");
                double ethPrice = parseNestedDouble(json, "ETH", "price");
                double ethChange = parseNestedDouble(json, "ETH", "change");

                String totalStr = String.format(Locale.US, "$%,.2f", totalUsd);
                String ethPriceStr = String.format(Locale.US, "ETH $%,.0f", ethPrice);
                String changeStr = String.format(Locale.US, "%s%.1f%%",
                    ethChange >= 0 ? "\u25B2" : "\u25BC", Math.abs(ethChange));
                int changeColor = ethChange >= 0 ? 0xFF4ADE80 : 0xFFF87171;

                String timeStr = new SimpleDateFormat("HH:mm", Locale.US).format(new Date());

                RemoteViews rv = new RemoteViews(context.getPackageName(), R.layout.widget_layout);
                rv.setTextViewText(R.id.total_usd, totalStr);
                rv.setTextViewText(R.id.eth_price, ethPriceStr);
                rv.setTextViewText(R.id.eth_change, changeStr);
                rv.setTextColor(R.id.eth_change, changeColor);
                rv.setTextViewText(R.id.updated_at, timeStr);
                rv.setOnClickPendingIntent(R.id.widget_root, pendingBrowser);

                appWidgetManager.updateAppWidget(widgetId, rv);

            } catch (Exception e) {
                Log.e("WalletWidget", "Fetch failed: " + e.getMessage());
                RemoteViews rv = new RemoteViews(context.getPackageName(), R.layout.widget_layout);
                rv.setTextViewText(R.id.total_usd, "$---.--");
                rv.setTextViewText(R.id.updated_at, "Offline");
                rv.setOnClickPendingIntent(R.id.widget_root, pendingBrowser);
                appWidgetManager.updateAppWidget(widgetId, rv);
            }
        }).start();
    }

    private static double parseDouble(String json, String key) {
        try {
            String search = "\"" + key + "\":";
            int idx = json.indexOf(search);
            if (idx < 0) return 0;
            idx += search.length();
            int end = idx;
            while (end < json.length() && (Character.isDigit(json.charAt(end)) || json.charAt(end) == '.' || json.charAt(end) == '-')) end++;
            return Double.parseDouble(json.substring(idx, end));
        } catch (Exception e) { return 0; }
    }

    private static double parseNestedDouble(String json, String outer, String inner) {
        try {
            String search = "\"" + outer + "\":";
            int idx = json.indexOf(search);
            if (idx < 0) return 0;
            String sub = json.substring(idx);
            return parseDouble(sub, inner);
        } catch (Exception e) { return 0; }
    }
}
```

### Step 7: Build the APK

Build entirely from command line — no Gradle or Android Studio needed. This produces a ~10KB APK.

**IMPORTANT BUILD GOTCHAS:**
- **UNC paths break aapt2/d8**: If sources are on WSL (`\\wsl.localhost\...`), copy them to a Windows-local path first
- **aapt2 compile must use `-o <directory>`**, not `-o <file>` (file mode creates wrong archive format)
- **aapt2 compile: do NOT use `--dir`** — it silently produces no output in some cases. Compile files one-by-one instead
- **d8.bat fails with JDK 17**: Call `java -cp d8.jar com.android.tools.r8.D8` directly instead of using d8.bat
- **Use apksigner, not jarsigner**: Android 13+ requires v2+ signatures (jarsigner only does v1)
- **Use `127.0.0.1` not `localhost`** in the Java code — `localhost` causes SocketTimeoutException from widget processes

#### PowerShell build script (rebuild.ps1)

Create this in the project directory. Adjust paths for your setup:

```powershell
$env:JAVA_HOME = "C:\Users\<USER>\Android\jdk17\jdk-17.0.2"
$JAVA = "$env:JAVA_HOME\bin\java.exe"
$BT = "C:\Users\<USER>\Android\Sdk\build-tools\33.0.2"
$PLAT = "C:\Users\<USER>\Android\Sdk\platforms\android-33\android.jar"
$SDK = "C:\Users\<USER>\Android\Sdk"
$LOCAL = "C:\Users\<USER>\Android\wallet-widget-build"
$SRC = "\\wsl.localhost\Ubuntu\tmp\wallet-widget"

Set-Location "C:\Users\<USER>\Android"

Write-Host "=== Copy updated sources ==="
Remove-Item -Recurse -Force "$LOCAL" -ErrorAction SilentlyContinue
Copy-Item -Recurse "$SRC\res" "$LOCAL\res"
Copy-Item -Recurse "$SRC\src" "$LOCAL\src"
Copy-Item "$SRC\AndroidManifest.xml" "$LOCAL\AndroidManifest.xml"
New-Item -ItemType Directory -Force -Path "$LOCAL\build\compiled" | Out-Null
New-Item -ItemType Directory -Force -Path "$LOCAL\build\gen" | Out-Null
New-Item -ItemType Directory -Force -Path "$LOCAL\build\classes" | Out-Null
New-Item -ItemType Directory -Force -Path "$LOCAL\build\dex" | Out-Null

Write-Host "=== Step 1: aapt2 compile ==="
Get-ChildItem "$LOCAL\res" -Recurse -File | ForEach-Object {
    & "$BT\aapt2.exe" compile $_.FullName -o "$LOCAL\build\compiled" 2>&1
}
$flatCount = (Get-ChildItem "$LOCAL\build\compiled\*.flat" | Measure-Object).Count
Write-Host "  $flatCount flat files compiled"

Write-Host "=== Step 2: aapt2 link ==="
$flatFiles = Get-ChildItem "$LOCAL\build\compiled\*.flat" | ForEach-Object { $_.FullName }
& "$BT\aapt2.exe" link -o "$LOCAL\build\base.apk" --manifest "$LOCAL\AndroidManifest.xml" -I $PLAT --java "$LOCAL\build\gen" --auto-add-overlay $flatFiles 2>&1
if (!(Test-Path "$LOCAL\build\base.apk")) { Write-Host "LINK FAILED"; exit 1 }
Write-Host "  Linked OK"

Write-Host "=== Step 3: javac ==="
& "$env:JAVA_HOME\bin\javac.exe" -source 11 -target 11 -classpath $PLAT -d "$LOCAL\build\classes" "$LOCAL\src\com\clawphone\wallet\WalletWidgetProvider.java" "$LOCAL\build\gen\com\clawphone\wallet\R.java" 2>&1
Write-Host "  Compiled OK"

Write-Host "=== Step 4: d8 (dex) ==="
$classFiles = Get-ChildItem "$LOCAL\build\classes" -Recurse -Filter "*.class" | ForEach-Object { $_.FullName }
& $JAVA -cp "$BT\lib\d8.jar" com.android.tools.r8.D8 --output "$LOCAL\build\dex" $classFiles 2>&1
Write-Host "  DEX OK"

Write-Host "=== Step 5: Add DEX to APK ==="
Set-Location "$LOCAL\build\dex"
& "$BT\aapt.exe" add "$LOCAL\build\base.apk" classes.dex 2>&1
Set-Location "C:\Users\<USER>\Android"

Write-Host "=== Step 6: zipalign ==="
& "$BT\zipalign.exe" -f 4 "$LOCAL\build\base.apk" "$LOCAL\build\wallet-widget.apk" 2>&1

Write-Host "=== Step 7: apksigner ==="
$ks = "$LOCAL\build\debug.keystore"
if (!(Test-Path $ks)) {
    & "$env:JAVA_HOME\bin\keytool.exe" -genkey -v -keystore $ks -storepass android -alias debug -keypass android -keyalg RSA -keysize 2048 -validity 10000 -dname "CN=Debug" 2>&1 | Out-Null
}
& $JAVA -jar "$BT\lib\apksigner.jar" sign --ks $ks --ks-pass "pass:android" --key-pass "pass:android" --ks-key-alias debug "$LOCAL\build\wallet-widget.apk" 2>&1

Write-Host "=== Step 8: Install ==="
& "$SDK\platform-tools\adb.exe" install -r "$LOCAL\build\wallet-widget.apk" 2>&1

Write-Host "=== DONE ==="
```

Run with: `powershell.exe -ExecutionPolicy Bypass -File rebuild.ps1`

**If install fails with INSTALL_FAILED_UPDATE_INCOMPATIBLE:** Run `adb uninstall com.clawphone.wallet` first (happens when keystore changes between builds).

### Step 8: Add widget to home screen

After installing, add the widget to the home screen:

1. Long-press on an empty area of the home screen
2. Tap "Widgets"
3. Scroll down to find "Wallet Widget" (green circle icon)
4. Tap to expand, then long-press and drag the widget preview onto the home screen

**Via ADB (UI automation):**
```bash
# Long press home screen
adb shell input swipe 540 1200 540 1200 1500
# Wait, then tap Widgets (use uiautomator dump to find exact coordinates)
# Scroll to Wallet Widget, then use input draganddrop to place it
```

## API Endpoints

- `GET http://localhost:8787` - Full HTML dashboard with auto-refresh
- `GET http://localhost:8787/api` - Raw JSON data for the widget

API response format:
```json
{
  "balances": {
    "solana": [],
    "ethereum": [{"address": "0x...", "label": "Main", "balance": 0.41, "usd": 800.92}],
    "totalUsd": 800.92
  },
  "prices": {
    "SOL": {"price": 79, "change": -6.4},
    "ETH": {"price": 1935, "change": -5.0}
  },
  "updated": "12:23:12 AM"
}
```

## Termux Info

- **Install Termux** from F-Droid (not Play Store - the Play Store version is outdated)
- **Required packages:** `pkg install nodejs` (Node.js 18+ for fetch API)
- **Optional packages:**
  - `pkg install termux-api` - for Android notifications
  - **Termux:Boot** from F-Droid - for auto-start on boot
  - **Termux:Widget** from F-Droid - for home screen shortcuts
- **Keep alive:** Run `termux-wake-lock` to prevent Android from killing the process
- **Battery impact:** Minimal. Server is idle between refreshes.

## Known Issues & Fixes

- **Do NOT use Node.js `https` module** - Has DNS/TLS issues in Termux/Android emulators. Use `fetch()` (Node 18+).
- **Etherscan API V1 is deprecated** - Use `eth.llamarpc.com` public JSON-RPC instead (no API key).
- **Widget must use `127.0.0.1` not `localhost`** - `localhost` causes SocketTimeoutException from Android widget processes. Always use the IP.
- **Server must bind to `0.0.0.0`** - Node.js defaults to `::` (IPv6 only). The Android widget connects via IPv4 `127.0.0.1`, so the server MUST use `server.listen(PORT, '0.0.0.0', ...)` to listen on IPv4.
- **network_security_config.xml is required** - Without it, Android 9+ silently blocks cleartext HTTP to localhost.
- **aapt2 compile: use file-by-file, not `--dir`** - `--dir` silently fails in some build-tools versions.
- **d8.bat broken with JDK 17** - Uses removed `-Djava.ext.dirs`. Call `java -cp d8.jar com.android.tools.r8.D8` directly.
- **Solana RPC** (`api.mainnet-beta.solana.com`) is rate-limited. For heavy use, consider a dedicated provider.
- **CoinGecko free tier** allows ~30 calls/min. Fine with 5-min refresh.

## Extending This Skill

- **More chains:** Add Bitcoin, Polygon, Arbitrum, Base balances
- **Token balances:** Fetch SPL tokens or ERC-20 tokens
- **Price alerts:** `termux-notification --title "SOL Alert" --content "SOL crossed $200"`
- **Transaction history:** Show last 5 transactions
- **DeFi positions:** Fetch staking, LP positions from protocols

## Troubleshooting

- **Port in use:** `pkill -f "node.*server.js"` then restart. Or change PORT.
- **Widget shows "Offline":** Make sure server.js is running in Termux, and the widget Java uses `127.0.0.1` (not `localhost`).
- **INSTALL_FAILED_UPDATE_INCOMPATIBLE:** `adb uninstall com.clawphone.wallet` then reinstall (keystore changed).
- **CoinGecko rate limit:** Prices show $0. Wait a few minutes or increase REFRESH_SECONDS.
- **fetch is not defined:** Node.js too old. Need 18+. `pkg upgrade nodejs`
- **Network errors in emulator:** Restart the Node server. Emulator DNS can be flaky on first boot.
- **Logcat debugging:** `adb logcat -s WalletWidget:*` to see widget fetch logs.
