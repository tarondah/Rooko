import webview
import requests
import threading
import time
import os
import json
import re
import subprocess
import sys
import shutil

# ========= Config =========
def load_jsonc(path):
    with open(path, "r") as f:
        text = f.read()
    # Remove // comments
    text = re.sub(r'//.*', '', text)
    return json.loads(text)

user_config = os.path.expanduser(r"~\Rooko\config.jsonc")
if not os.path.exists(user_config):
    os.makedirs(os.path.dirname(user_config), exist_ok=True)
    shutil.copy("config.jsonc", user_config)

config = load_jsonc(user_config)


USERNAME = config.get("USERNAME", "")
SHOW_GRAPH = config.get("SHOW_GRAPH", True)
EMAIL = config.get("EMAIL", "example@example.com")
PLAYTIME_FILE = config.get("PLAYTIME_FILE", "playtime.txt")
is_fullscreen = False
ICON_PATH = r"D:\Projects\Blender Add-on\logo.ico"
HEADERS = {
    "User-Agent": f"ChessClient/1.0 (username:{USERNAME}; contact:{EMAIL})"
}

def open_config_file():
    original_path = os.path.abspath("config.jsonc")
    # Use a writable location in the user's home folder
    user_config_dir = os.path.join(os.path.expanduser("~"), "Rooko")
    os.makedirs(user_config_dir, exist_ok=True)
    user_config_path = os.path.join(user_config_dir, "config.jsonc")

    # Copy the original config if it doesn't exist in the writable location
    if not os.path.exists(user_config_path):
        shutil.copy(original_path, user_config_path)

    try:
        if sys.platform.startswith("win"):
            os.startfile(user_config_path)
        elif sys.platform.startswith("darwin"):
            subprocess.call(["open", user_config_path])
        else:
            subprocess.call(["xdg-open", user_config_path])
    except Exception as e:
        print("Could not open config file:", e)

# ========= Playtime Tracker =========
playtime_seconds = 0
playtime_running = False

# Load previous total playtime
if os.path.exists(PLAYTIME_FILE):
    with open(PLAYTIME_FILE, "r") as f:
        try:
            playtime_seconds = int(f.read())
        except:
            playtime_seconds = 0

def save_playtime():
    with open(PLAYTIME_FILE, "w") as f:
        f.write(str(playtime_seconds))

def track_playtime(window: webview.Window):
    global playtime_seconds, playtime_running
    playtime_running = True
    while playtime_running:
        try:
            url = window.get_current_url() or ""
            if "chess.com/play" in url:
                playtime_seconds += 1
            else:
                # save when leaving chess.com/play
                save_playtime()
        except Exception as e:
            print("Playtime tracker error:", e)
        time.sleep(1)

def format_playtime(seconds):
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

# ========= Fullscreen =========
def toggle_fullscreen(window):
    global is_fullscreen
    is_fullscreen = not is_fullscreen
    window.toggle_fullscreen()

# ========= Data Fetching =========
def get_player_stats(username: str):
    """
    Returns: bullet, blitz, rapid, win_rate(last 10), streak(int: +wins / -losses), rating_trend(list)
    """
    try:
        stats_url = f"https://api.chess.com/pub/player/{username}/stats"
        archives_url = f"https://api.chess.com/pub/player/{username}/games/archives"

        stats = requests.get(stats_url, headers=HEADERS, timeout=10).json()

        bullet = stats.get("chess_bullet", {}).get("last", {}).get("rating", None)
        blitz  = stats.get("chess_blitz",  {}).get("last", {}).get("rating", None)
        rapid  = stats.get("chess_rapid",  {}).get("last", {}).get("rating", None)

        # Latest month archive -> recent games
        archives = requests.get(archives_url, headers=HEADERS, timeout=10).json().get("archives", [])
        if not archives:
            return bullet, blitz, rapid, None, 0, []

        latest_month_url = archives[-1]
        games = requests.get(latest_month_url, headers=HEADERS, timeout=10).json().get("games", [])
        if not games:
            return bullet, blitz, rapid, None, 0, []

        recent_games = games[-10:]

        wins = 0
        streak = 0
        last_result = None
        rating_trend = []

        for g in recent_games:
            you_are_white = g["white"]["username"].lower() == username.lower()
            side = "white" if you_are_white else "black"
            result = g[side].get("result")
            rating_trend.append(g[side].get("rating", blitz or bullet or rapid or 0))

            if result == "win":
                wins += 1
                streak = streak + 1 if last_result == "win" else 1
            elif result == "loss":
                streak = streak - 1 if last_result == "loss" else -1
            last_result = result

        win_rate = round((wins / len(recent_games)) * 100, 1) if recent_games else None
        return bullet, blitz, rapid, win_rate, streak, rating_trend
    except Exception as e:
        print("Error fetching stats:", e)
        return None, None, None, None, 0, []

def sparkline_chart(data):
    """Unicode sparkline for rating trend."""
    if not SHOW_GRAPH or not data:
        return ""
    max_r = max(data)
    min_r = min(data)
    bars = ["▁","▂","▃","▄","▅","▆","▇","█"]
    out = []
    for r in data:
        if max_r == min_r:
            out.append(bars[0])
        else:
            idx = int((r - min_r) / (max_r - min_r) * (len(bars)-1))
            out.append(bars[idx])
    return "".join(out)

# ========= In-game Overlay Injection =========
def build_overlay_text():
    bullet, blitz, rapid, win_rate, streak, trend = get_player_stats(USERNAME)
    streak_emoji = "🔥" if streak > 0 else "❄️" if streak < 0 else "➖"
    streak_text = f"{streak_emoji} {abs(streak)}" if streak_emoji != "➖" else "0"
    graph = sparkline_chart(trend)
    # Two lines: ratings main line + optional graph/streak line
    main = f"You ⚡{bullet or 'N/A'}  🔥{blitz or 'N/A'}  ⏳{rapid or 'N/A'}  🏆{win_rate or 'N/A'}%"
    sub  = f"📊 {graph}   Streak: {streak_text}" if graph else f"Streak: {streak_text}"
    return f"{main}\n{sub}"

def inject_stats_bar(window: webview.Window):
    stats_html = build_overlay_text()

    js_code = f"""
    (function() {{
        let bar = document.getElementById('custom-stats-bar');
        if (!bar) {{
            bar = document.createElement('div');
            bar.id = 'custom-stats-bar';
            bar.style.backgroundColor = '#262522';
            bar.style.color = '#fff';
            bar.style.padding = '8px 12px';
            bar.style.fontSize = '13px';
            bar.style.fontFamily = 'Arial, sans-serif';
            bar.style.borderRadius = '20px';
            bar.style.boxShadow = '0 2px 4px rgba(0,0,0,0.3)';
            bar.style.display = 'flex';
            bar.style.flexDirection = 'column';
            bar.style.alignItems = 'flex-start';
            bar.style.whiteSpace = 'pre';
            bar.style.margin = '8px';
            bar.style.gap = '6px';

            // Create text container
            let statsContainer = document.createElement('div');
            statsContainer.id = 'stats-text';

            // Create button
            let homeBtn = document.createElement('button');
            homeBtn.innerText = 'Home';
            homeBtn.style.background = 'transparent';
            homeBtn.style.border = '1px solid #fff';
            homeBtn.style.color = '#fff';
            homeBtn.style.padding = '4px 10px';
            homeBtn.style.borderRadius = '6px';
            homeBtn.style.cursor = 'pointer';
            homeBtn.style.fontSize = '13px';
            homeBtn.style.alignSelf = 'flex-start'; // left align
            homeBtn.addEventListener('click', () => {{
                // Send a message to Python to reload homepage
                window.pywebview.api.go_home();
            }});

            bar.appendChild(statsContainer);
            bar.appendChild(homeBtn);

            // Prefer sidebar next to the board; fall back to layout or body
            let sidebar = document.querySelector('.board-layout-sidebar') 
                          || document.querySelector('.board-layout')
                          || document.body;
            sidebar.insertBefore(bar, sidebar.firstChild);
        }}

        // Update stats text
        let statsDiv = document.getElementById('stats-text');
        if (statsDiv) statsDiv.textContent = `{stats_html}`;
    }})();
    """
    window.evaluate_js(js_code)




def keep_stats_updated(window: webview.Window):
    """Only inject when on chess.com page. Poll every 30s."""
    while True:
        try:
            url = window.get_current_url() or ""
            if "chess.com" in url:
                inject_stats_bar(window)

        except Exception as e:
            print("Error updating stats:", e)
        time.sleep(5)

# ========= Homepage (HTML in same window) =========
def build_home_html():
    bullet, blitz, rapid, win_rate, streak, trend = get_player_stats(USERNAME)
    streak_emoji = "🔥" if streak > 0 else "❄️" if streak < 0 else "➖"
    streak_text = f"{streak_emoji} {abs(streak)}" if streak_emoji != "➖" else "0"
    chart = sparkline_chart(trend)

    # f-string: double braces for CSS
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8" />
      <title>Rooko Dashboard</title>
      <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
      <style>
        :root {{
          --bg: #1e1e1e;
          --panel: #262522;
          --panel-2: #2f2e2b;
          --text: #ffffff;
          --accent: #81b64c;
          --accent-hover: #6aa13b;
          --muted: #bdbdbd;
        }}
        * {{ box-sizing: border-box; }}
        body {{
          margin: 0;
          background: var(--bg);
          color: var(--text);
          font-family: Arial, sans-serif;
        }}
        header {{
          position: sticky;
          top: 0;
          background: var(--panel);
          padding: 18px 20px;
          box-shadow: 0 2px 6px rgba(0,0,0,.35);
          z-index: 10;
        }}
        .wrap {{ max-width: 980px; margin: 0 auto; }}
        h1 {{ margin: 0; font-size: 22px; font-weight: 600; letter-spacing: .3px; }}
        .cards {{
          display: grid;
          grid-template-columns: repeat(3, minmax(0, 1fr));
          gap: 14px;
          margin: 18px 0;
        }}
        .card {{
          background: var(--panel-2);
          padding: 18px;
          border-radius: 14px;
          box-shadow: 0 2px 6px rgba(0,0,0,.35);
          display: flex; flex-direction: column; align-items: center; justify-content: center;
        }}
        .card h2 {{ margin: 0 0 8px 0; font-size: 14px; color: var(--muted); }}
        .value {{ font-size: 28px; font-weight: 700; letter-spacing: .5px; }}
        .big-panel {{
          background: var(--panel);
          padding: 18px;
          border-radius: 14px;
          box-shadow: 0 2px 6px rgba(0,0,0,.35);
          margin-top: 8px;
        }}
        .rows {{ display: grid; gap: 8px; }}
        .row {{ display: flex; justify-content: space-between; font-size: 15px; }}
        .chart {{ font-size: 22px; text-align: center; margin-top: 8px; color: #9be18b; }}
        .btns {{ display: flex; gap: 10px; margin-top: 18px; }}
        .btn {{
          appearance: none; border: 0; outline: 0; cursor: pointer;
          padding: 12px 16px; border-radius: 10px; font-size: 15px; font-weight: 600;
          background: var(--accent); color: #fff; text-decoration: none; text-align: center; flex: 1;
        }}
        .btn:hover {{ background: var(--accent-hover); }}
        .muted {{ color: var(--muted); font-size: 13px; text-align:center; margin-top: 6px; }}
        @media (max-width: 760px) {{
          .cards {{ grid-template-columns: 1fr; }}
        }}
      </style>
    </head>
    <body>
      <header>
        <div class="wrap">
          <h1>♟ Rooko Dashboard</h1>
        </div>
      </header>
      <main class="wrap">
        <section class="cards">
          <div class="card">
            <h2>⚡ Bullet</h2>
            <div class="value">{bullet or "N/A"}</div>
          </div>
          <div class="card">
            <h2>🔥 Blitz</h2>
            <div class="value">{blitz or "N/A"}</div>
          </div>
          <div class="card">
            <h2>⏳ Rapid</h2>
            <div class="value">{rapid or "N/A"}</div>
          </div>
        </section>

        <section class="big-panel">
          <div class="rows">
            <div class="row"><span>🏆 Win Rate (last 10)</span><strong>{win_rate or "N/A"}%</strong></div>
            <div class="row"><span>Streak</span><strong>{streak_text}</strong></div>
            <div class="row"><span>⏱ Total Playtime</span><strong>{format_playtime(playtime_seconds)}</strong></div>
          </div>
          <div class="chart">{chart}</div>

          <div class="btns">
            <a class="btn" href="https://www.chess.com/play" target="_self">▶ Go Play</a>
            <a class="btn" href="https://www.chess.com/member/{USERNAME}" target="_self">Profile</a>
            <button class="btn" onclick="pywebview.api.toggleFullscreen()">⛶ Fullscreen</button>
            <button class="btn" onclick="pywebview.api.openConfig()">⚙ Edit Config</button>


          </div>
          <div class="muted">&#169; Taron Dahn</div>
        </section>
      </main>
    </body>
    </html>
    """

# ========= App Wiring (one window, both modes) =========
def url_watchdog(window: webview.Window):
    injector_started = False
    while True:
        try:
            url = window.get_current_url() or ""
            on_chess = "chess.com/play" in url
            if on_chess and not injector_started:
                threading.Thread(target=keep_stats_updated, args=(window,), daemon=True).start()
                injector_started = True
        except Exception as e:
            print("URL watchdog error:", e)
        time.sleep(1.0)

if __name__ == "__main__":
    class Api:
        def go_home(self):
            html = build_home_html()
            webview.windows[0].load_html(html)
        def toggleFullscreen(self):
            toggle_fullscreen(win)
        def openConfig(self):
            open_config_file()

    api_instance = Api()

    # Start on the custom homepage
    html = build_home_html()
    win = webview.create_window(
        f"Rooko",
        html=build_home_html(),
        width=1100,
        height=800,
        js_api=api_instance
    )

    def on_loaded():
        # Start a small watchdog that waits until you navigate to chess.com/play
        threading.Thread(target=url_watchdog, args=(win,), daemon=True).start()
        threading.Thread(target=track_playtime, args=(win,), daemon=True).start()

    webview.start(func=on_loaded, private_mode=False)
