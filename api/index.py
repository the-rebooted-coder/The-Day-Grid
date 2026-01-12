from flask import Flask, send_file, request
import datetime
import calendar
from PIL import Image, ImageDraw, ImageFont
import io
import os

app = Flask(__name__)

# --- Configuration & Themes ---
IMAGE_WIDTH = 1170
IMAGE_HEIGHT = 2532

# Default (Year) Grid Settings
GRID_COLS = 15
GRID_ROWS = 25
DOT_RADIUS = 18
DOT_PADDING = 15

# Define Color Palettes
THEMES = {
    'dark': {
        'BG': (28, 28, 30),
        'ACTIVE': (255, 105, 60),    # Orange
        'PASSED': (255, 255, 255),   # White
        'INACTIVE': (68, 68, 70),    # Dim Gray
        'SPECIAL': (255, 215, 0),    # Gold
        'TEXT': (255, 255, 255)      # White Text
    },
    'light': {
        'BG': (242, 242, 247),       # iOS Light Gray
        'ACTIVE': (255, 105, 60),    # Orange
        'PASSED': (60, 60, 67),      # Dark Gray (Completed)
        'INACTIVE': (209, 209, 214), # Light Gray (Future)
        'SPECIAL': (255, 204, 0),    # Gold
        'TEXT': (0, 0, 0)            # Black Text
    }
}

# Font Paths
FONT_DIR = os.path.join(os.path.dirname(__file__), 'fonts')
FONT_PATH = os.path.join(FONT_DIR, 'Roboto-Regular.ttf')
FONT_SIGNATURE_PATH = os.path.join(FONT_DIR, 'Buffalo.otf')

# --- THE DASHBOARD ---
HTML_DASHBOARD = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>The Grid Generator</title>
    <meta name="description" content="Visualize your year. A minimal wallpaper generator for iOS.">

    <meta property="og:type" content="website">
    <meta property="og:url" content="https://the-day-grid.vercel.app/">
    <meta property="og:title" content="The Grid.">
    <meta property="og:description" content="Visualize your year. Don't waste it.">
    <meta property="og:image" content="https://the-day-grid.vercel.app/api/image?theme=dark&mode=year&bar_style=segmented">

    <meta property="twitter:card" content="summary_large_image">
    <meta property="twitter:url" content="https://the-day-grid.vercel.app/">
    <meta property="twitter:title" content="The Grid.">
    <meta property="twitter:description" content="Visualize your year. Don't waste it.">
    <meta property="twitter:image" content="https://the-day-grid.vercel.app/api/image?theme=dark&mode=year&bar_style=segmented">
    
    <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><circle cx=%2250%22 cy=%2250%22 r=%2250%22 fill=%22%23ff693c%22/></svg>">
    <link rel="apple-touch-icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><rect width=%22100%22 height=%22100%22 fill=%22%231c1c1e%22/><circle cx=%2250%22 cy=%2250%22 r=%2240%22 fill=%22%23ff693c%22/></svg>">

    <script defer src="/_vercel/insights/script.js"></script>

    <style>
        /* SCROLL FIX */
        body { 
            background: #1c1c1e; 
            color: white; 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; 
            display: flex; 
            flex-direction: column; 
            align-items: center; 
            min-height: 100dvh; 
            margin: 0; 
            padding: 10vh 20px 40px 20px; 
            box-sizing: border-box; 
            overflow-x: hidden; 
        }

        .header-section { margin-bottom: 30px; text-align: center; width: 100%; }
        h1 { font-weight: 900; letter-spacing: -1px; margin: 0 0 5px 0; font-size: 2.5rem; }
        .subtitle-container { display: flex; align-items: center; justify-content: center; gap: 8px; }
        p.subtitle { color: #888; text-align: center; line-height: 1.5; font-size: 0.95rem; margin: 0; }
        
        .info-btn { background: none; border: 1px solid #444; color: #888; border-radius: 50%; width: 20px; height: 20px; font-size: 12px; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.2s; font-family: serif; font-weight: bold; }
        .info-btn:hover { border-color: #ff693c; color: #ff693c; }

        .content-wrapper { flex-grow: 1; display: flex; flex-direction: column; align-items: center; width: 100%; max-width: 330px; margin-bottom: 40px; }

        button.generate-btn { background: #ff693c; color: white; border: none; padding: 15px 30px; border-radius: 12px; font-weight: bold; font-size: 16px; cursor: pointer; width: 100%; transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1); box-shadow: 0 4px 15px rgba(255, 105, 60, 0.3); }
        button.generate-btn:hover { opacity: 0.9; }
        button.generate-btn.success { background: #34c759 !important; box-shadow: 0 4px 15px rgba(52, 199, 89, 0.3); transform: scale(0.98); }
        button.generate-btn:disabled { background: #333 !important; color: #666 !important; box-shadow: none !important; cursor: not-allowed; opacity: 1; }

        .separator { display: flex; align-items: center; justify-content: center; width: 100%; margin: 25px 0; color: #555; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; }
        .separator::before, .separator::after { content: ""; flex: 1; border-bottom: 1px solid #333; margin: 0 10px; }

        .customise-trigger { color: #888; background: #252527; border: 1px solid #333; padding: 12px 20px; border-radius: 12px; font-size: 0.9rem; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 8px; transition: all 0.2s; font-weight: 500; width: 100%; box-sizing: border-box; }
        .customise-trigger:hover { background: #333; color: white; border-color: #555; }
        .arrow { font-size: 0.7rem; transition: transform 0.3s; }
        .customise-trigger.active .arrow { transform: rotate(180deg); }

        #custom-section { display: none; width: 100%; animation: slideDown 0.3s ease; border: 1px solid #333; border-radius: 12px; padding: 15px; margin-top: 10px; background: #232325; box-sizing: border-box; }
        
        h2 { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1px; color: #666; margin: 0 0 10px 0; }

        #date-list { display: flex; flex-direction: column; gap: 8px; margin-bottom: 15px; }
        .date-row { display: flex; gap: 10px; align-items: center; }
        
        input[type="date"], input[type="text"], select { background: #2c2c2e; border: 1px solid #444; padding: 10px; border-radius: 8px; color: white; flex-grow: 1; font-family: inherit; font-size: 14px; outline: none; transition: border 0.2s; color-scheme: dark; width: 100%; box-sizing: border-box; }
        input[type="date"]:focus, input[type="text"]:focus, select:focus { border-color: #ff693c; }
        
        .btn-icon { background: #333; border: 1px solid #444; width: 38px; height: 38px; border-radius: 8px; display: flex; align-items: center; justify-content: center; cursor: pointer; color: #ff693c; font-size: 18px; flex-shrink: 0; }
        .btn-icon:hover { background: #444; }

        .btn-add { background: transparent; border: 1px dashed #444; color: #888; width: 100%; padding: 8px; border-radius: 8px; cursor: pointer; font-size: 13px; margin-bottom: 15px; transition: all 0.2s; }
        .btn-add:hover { border-color: #ff693c; color: #ff693c; }

        .theme-switch { display: flex; gap: 10px; background: #2c2c2e; padding: 4px; border-radius: 8px; width: 100%; box-sizing: border-box; margin-bottom: 15px; }
        .theme-option { flex: 1; text-align: center; padding: 8px; border-radius: 6px; cursor: pointer; font-weight: 600; font-size: 13px; color: #888; transition: all 0.2s; }
        .theme-option.active { background: #444; color: white; }
        input[type="radio"] { display: none; }
        
        button.generate-custom-btn { background: #333; color: white; border: 1px solid #555; padding: 12px; border-radius: 8px; font-weight: bold; font-size: 14px; cursor: pointer; width: 100%; transition: all 0.2s; }
        button.generate-custom-btn:hover { background: #ff693c; border-color: #ff693c; }

        .result { margin-top: 20px; display: none; text-align: center; animation: slideUp 0.5s ease; width: 100%; border-top: 1px solid #333; padding-top: 20px; }
        .default-success { color: #ff693c; font-weight: bold; font-size: 1.1rem; margin-bottom: 20px; display: none; }
        .mock-msg { color: #ff453a; font-size: 0.85rem; margin-bottom: 20px; line-height: 1.4; display: none; border: 1px solid #ff453a; padding: 12px; border-radius: 12px; background: rgba(255, 69, 58, 0.1); text-align: left; }
        .custom-url-display { display: none; }

        .url-container { display: flex; gap: 10px; margin: 10px 0; }
        .url-box { background: #000; padding: 12px; border-radius: 8px; font-family: monospace; font-size: 13px; color: #ff693c; border: 1px solid #333; flex-grow: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .copy-btn { background: #333; border: 1px solid #444; border-radius: 8px; cursor: pointer; color: white; padding: 0 15px; font-weight: bold; transition: background 0.2s; }
        
        .shortcut-section { margin-top: 20px; background: #2c2c2e; padding: 15px; border-radius: 12px; border: 1px solid #444; }
        .shortcut-btn { background: white; color: black; display: block; width: 100%; padding: 12px; border-radius: 8px; font-weight: bold; text-decoration: none; margin-top: 10px; box-sizing: border-box; }
        a.preview-link { color: #ff693c; text-decoration: none; font-weight: 600; display: inline-block; margin-top: 10px; font-size: 0.9rem; }
        
        footer { margin-top: auto; color: #555; font-family: 'Courier New', monospace; font-size: 13px; opacity: 0.8; padding-bottom: 10px; width: 100%; text-align: center; }
        .footer-link { color: #555; text-decoration: none; border-bottom: 1px dotted #555; transition: color 0.2s; }
        .footer-link:hover { color: #ff693c; border-color: #ff693c; }

        .modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0, 0, 0, 0.7); backdrop-filter: blur(5px); z-index: 1000; display: none; align-items: center; justify-content: center; opacity: 0; transition: opacity 0.3s; }
        .modal { background: #1c1c1e; border: 1px solid #333; padding: 25px; border-radius: 16px; width: 90%; max-width: 320px; transform: scale(0.9); transition: transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275); box-shadow: 0 20px 50px rgba(0,0,0,0.5); }
        .modal h3 { margin-top: 0; color: white; text-align: center; }
        .color-legend { display: flex; flex-direction: column; gap: 15px; margin-top: 20px; }
        .legend-item { display: flex; align-items: center; gap: 15px; font-size: 0.95rem; color: #ccc; }
        .dot { width: 16px; height: 16px; border-radius: 50%; display: inline-block; flex-shrink: 0; }
        .dot.white { background: #fff; border: 1px solid #444; }
        .dot.orange { background: #ff693c; box-shadow: 0 0 8px rgba(255, 105, 60, 0.6); }
        .dot.yellow { background: #ffd700; box-shadow: 0 0 8px rgba(255, 215, 0, 0.6); }
        .dot.gray { background: #444446; }
        .close-modal { background: #333; border: none; color: white; width: 100%; padding: 12px; border-radius: 10px; margin-top: 25px; cursor: pointer; font-weight: 600; }

        @keyframes slideDown { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes slideUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
    </style>
</head>
<body>
    <div class="header-section">
        <h1>The Grid.</h1>
        <div class="subtitle-container">
            <p class="subtitle">Visualize your year.</p>
            <button class="info-btn" onclick="openModal()" title="What do the colors mean?">i</button>
        </div>
    </div>
    
    <div class="content-wrapper">
        <button class="generate-btn" id="default-btn" onclick="generateDefault()">Get The Grid</button>

        <div class="separator">OR</div>

        <div class="customise-trigger" onclick="toggleCustomise(this)">
            <span>Customise</span>
            <span class="arrow">▼</span>
        </div>

        <div id="custom-section">
            <h2>View Mode</h2>
            <div style="margin-bottom: 20px;">
                <select id="view-mode">
                    <option value="year">Full Year (Default)</option>
                    <option value="quarter">Current Quarter</option>
                    <option value="month">Current Month</option>
                    <option value="fortnight">Fortnight (14 Days)</option>
                </select>
            </div>

            <h2>Progress Bar Style</h2>
            <div style="margin-bottom: 20px;">
                <select id="bar-style">
                    <option value="segmented">Segmented (Default)</option>
                    <option value="solid">Solid</option>
                    <option value="minimal">Minimal</option>
                </select>
            </div>

            <h2>Dates of Importance</h2>
            <div id="date-list">
                <div class="date-row">
                    <input type="date" class="date-input">
                    <button class="btn-icon btn-remove" onclick="removeDate(this)">×</button>
                </div>
            </div>
            <button class="btn-add" onclick="addDate()">+ Add another date</button>

            <h2>Theme</h2>
            <div class="theme-switch">
                <label class="theme-option active" id="lbl-dark" onclick="setTheme('dark')">
                    Dark
                    <input type="radio" name="theme" value="dark" checked>
                </label>
                <label class="theme-option" id="lbl-light" onclick="setTheme('light')">
                    Light
                    <input type="radio" name="theme" value="light">
                </label>
            </div>

            <h2>Signature</h2>
            <div style="margin-bottom: 20px;">
                <input type="text" id="signature" placeholder="Add your signature..." maxlength="20">
            </div>

            <button class="generate-custom-btn" onclick="generateCustom()">Generate Custom Link</button>
        </div>

        <div class="result" id="result">
            <div id="default-success" class="default-success">✓ Link Copied.</div>
            <div id="mock-msg" class="mock-msg">You expanded the custom menu, changed absolutely nothing, and hit generate. We copied the link anyway, but we're judging you.</div>

            <div id="custom-url-display" class="custom-url-display">
                <p style="margin-bottom: 5px; font-size: 0.9rem; color: #888;">Step 1: Copy this URL.</p>
                <div class="url-container">
                    <div class="url-box" id="urlBox"></div>
                    <button class="copy-btn" onclick="copyToClipboard()">Copy</button>
                </div>
                <a class="preview-link" id="previewLink" href="#" target="_blank">Preview Wallpaper →</a>
            </div>

            <div class="shortcut-section">
                <p style="margin: 0 0 10px 0; font-size: 0.9rem; color: #ccc;">Step 2: Install the Shortcut.</p>
                <p style="margin: 0 0 10px 0; font-size: 0.8rem; color: #888; line-height: 1.4;">
                    Since you probably need hand-holding: <strong>First add the shortcut, then click on the three dots (...) to edit it.</strong> Paste the URL where indicated. Don't mess it up.
                </p>
                <a href="https://www.icloud.com/shortcuts/99a190f4001844f9ade585fc8eafd47e" class="shortcut-btn" target="_blank">Install iOS Shortcut</a>
            </div>
        </div>
    </div>

    <footer>
        &lt;/&gt; with ❤️ by Spandan.<br>
        <a href="https://github.com/the-rebooted-coder/The-Day-Grid/tree/main" target="_blank" class="footer-link" style="font-size: 11px; margin-top: 5px; display: inline-block;">Version 1.0 Prod.</a>
    </footer>

    <div class="modal-overlay" id="modalOverlay" onclick="closeModal(event)">
        <div class="modal">
            <h3>The Legend</h3>
            <div class="color-legend">
                <div class="legend-item">
                    <span class="dot white"></span>
                    <span><strong>The Past:</strong> Gone. Wasted. Irrecoverable. Stop looking at it.</span>
                </div>
                <div class="legend-item">
                    <span class="dot orange"></span>
                    <span><strong>The Present:</strong> You are here. Try not to screw this one up.</span>
                </div>
                <div class="legend-item">
                    <span class="dot yellow"></span>
                    <span><strong>The "Special":</strong> Dates you think matter. You'll probably forget them.</span>
                </div>
                <div class="legend-item">
                    <span class="dot gray"></span>
                    <span><strong>The Void:</strong> The future. Try to fill it with something better than the white ones.</span>
                </div>
            </div>
            <button class="close-modal" onclick="toggleModal(false)">Whatever</button>
        </div>
    </div>

    <script>
        window.onload = function() {
            const isApple = /iPhone|iPad|iPod|Macintosh/i.test(navigator.userAgent);
            
            if (!isApple) {
                const btn = document.getElementById('default-btn');
                btn.innerText = "Sorry, currently available only on iOS / iPadOS";
                btn.disabled = true;
                
                document.querySelector('.separator').style.display = 'none';
                document.querySelector('.customise-trigger').style.display = 'none';
                document.getElementById('custom-section').style.display = 'none';
                
                document.querySelector('footer').style.marginTop = 'auto';
            }
        };

        let selectedTheme = 'dark';

        function toggleCustomise(trigger) {
            const section = document.getElementById('custom-section');
            if (section.style.display === 'block') {
                section.style.display = 'none';
                trigger.classList.remove('active');
            } else {
                section.style.display = 'block';
                trigger.classList.add('active');
            }
        }

        function openModal() { toggleModal(true); }
        function closeModal(e) { if(e.target === document.getElementById('modalOverlay')) toggleModal(false); }
        function toggleModal(show) {
            const overlay = document.getElementById('modalOverlay');
            const modal = overlay.querySelector('.modal');
            if (show) {
                overlay.style.display = 'flex';
                void overlay.offsetWidth;
                overlay.style.opacity = '1';
                modal.style.transform = 'scale(1)';
            } else {
                overlay.style.opacity = '0';
                modal.style.transform = 'scale(0.9)';
                setTimeout(() => { overlay.style.display = 'none'; }, 300);
            }
        }

        function addDate() {
            const container = document.getElementById('date-list');
            const div = document.createElement('div');
            div.className = 'date-row';
            div.innerHTML = `<input type="date" class="date-input"><button class="btn-icon btn-remove" onclick="removeDate(this)">×</button>`;
            container.appendChild(div);
        }
        function removeDate(btn) {
            const container = document.getElementById('date-list');
            if (container.children.length > 1) btn.parentElement.remove();
            else btn.parentElement.querySelector('input').value = '';
        }

        function setTheme(theme) {
            selectedTheme = theme;
            document.getElementById('lbl-dark').className = theme === 'dark' ? 'theme-option active' : 'theme-option';
            document.getElementById('lbl-light').className = theme === 'light' ? 'theme-option active' : 'theme-option';
        }

        function generateDefault() {
            const baseUrl = window.location.origin + "/api/image";
            const fullUrl = baseUrl + "?theme=dark";
            const btn = document.getElementById('default-btn');
            
            navigator.clipboard.writeText(fullUrl).then(() => {
                const originalText = btn.innerText;
                btn.innerText = "Link Copied";
                btn.classList.add("success");
                btn.disabled = true;

                document.getElementById('result').style.display = "block";
                document.getElementById('default-success').style.display = "block";
                document.getElementById('mock-msg').style.display = "none";
                document.getElementById('custom-url-display').style.display = "none";
                document.getElementById('custom-section').style.display = "none";
                document.querySelector('.customise-trigger').classList.remove('active');
                
                document.getElementById('result').scrollIntoView({ behavior: 'smooth' });

                setTimeout(() => { 
                    btn.innerText = originalText; 
                    btn.classList.remove("success");
                    btn.disabled = false;
                }, 2000);
            }).catch(err => {
                generateCustom();
            });
        }

        function generateCustom() {
            const inputs = document.querySelectorAll('.date-input');
            let dateArray = [];
            inputs.forEach(input => {
                if (input.value) {
                    const parts = input.value.split('-'); 
                    if (parts.length === 3) dateArray.push(`${parts[1]}-${parts[2]}`);
                }
            });

            const sig = document.getElementById('signature').value.trim();
            const mode = document.getElementById('view-mode').value;
            const barStyle = document.getElementById('bar-style').value;
            
            const val = dateArray.join(',');
            const baseUrl = window.location.origin + "/api/image";
            const params = new URLSearchParams();
            
            if (val) params.append('dates', val);
            params.append('theme', selectedTheme);
            if (sig) params.append('signature', sig);
            if (mode !== 'year') params.append('mode', mode);
            if (barStyle !== 'segmented') params.append('bar_style', barStyle);
            
            const fullUrl = baseUrl + "?" + params.toString();
            const isDefault = dateArray.length === 0 && selectedTheme === 'dark' && sig === '' && mode === 'year' && barStyle === 'segmented';

            if (isDefault) {
                navigator.clipboard.writeText(fullUrl).then(() => {
                    document.getElementById('result').style.display = "block";
                    document.getElementById('default-success').style.display = "block";
                    document.getElementById('mock-msg').style.display = "block";
                    document.getElementById('custom-url-display').style.display = "none";
                    document.getElementById('result').scrollIntoView({ behavior: 'smooth' });
                });
            } else {
                document.getElementById('urlBox').innerText = fullUrl;
                document.getElementById('previewLink').href = fullUrl;
                document.getElementById('result').style.display = "block";
                document.getElementById('default-success').style.display = "none";
                document.getElementById('mock-msg').style.display = "none";
                document.getElementById('custom-url-display').style.display = "block";
                document.getElementById('result').scrollIntoView({ behavior: 'smooth' });
            }
        }

        function copyToClipboard() {
            const text = document.getElementById('urlBox').innerText;
            navigator.clipboard.writeText(text).then(() => {
                const btn = document.querySelector('.copy-btn');
                const originalText = btn.innerText;
                btn.innerText = "Copied!";
                btn.style.background = "#ff693c";
                setTimeout(() => { btn.innerText = originalText; btn.style.background = "#333"; }, 2000);
            });
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return HTML_DASHBOARD

@app.route('/api/image')
def generate_grid():
    # 1. Get Parameters
    dates_param = request.args.get('dates', '')
    theme_param = request.args.get('theme', 'dark')
    signature_param = request.args.get('signature', '')
    mode_param = request.args.get('mode', 'year')
    bar_style_param = request.args.get('bar_style', 'segmented')

    # 2. Select Theme Colors
    palette = THEMES.get(theme_param, THEMES['dark'])
    
    # 3. Setup Time (IST)
    ist_offset = datetime.timedelta(hours=5, minutes=30)
    now = datetime.datetime.now(datetime.timezone.utc) + ist_offset
    current_year = now.year
    
    # 4. Determine Grid Dimensions & Range based on Mode
    # Default Year Logic
    grid_cols = GRID_COLS
    grid_rows = GRID_ROWS
    dot_radius = DOT_RADIUS
    dot_spacing = DOT_PADDING
    
    # Dates logic
    if mode_param == 'month':
        start_date = datetime.date(current_year, now.month, 1)
        last_day = calendar.monthrange(current_year, now.month)[1]
        end_date = datetime.date(current_year, now.month, last_day)
        
        # Month View (Revised Math for Center)
        grid_cols = 7
        grid_rows = 5
        dot_radius = 35 
        dot_spacing = 45
        
    elif mode_param == 'quarter':
        # Calculate Quarter
        q = (now.month - 1) // 3 + 1
        start_month = (q - 1) * 3 + 1
        end_month = start_month + 2
        
        start_date = datetime.date(current_year, start_month, 1)
        last_day_q = calendar.monthrange(current_year, end_month)[1]
        end_date = datetime.date(current_year, end_month, last_day_q)
        
        # Quarter View
        grid_cols = 10
        grid_rows = 10 
        dot_radius = 25 
        dot_spacing = 25
        
    elif mode_param == 'fortnight':
        # 14 Days starting from the most recent Monday
        start_date = now.date() - datetime.timedelta(days=now.weekday())
        end_date = start_date + datetime.timedelta(days=13)
        
        # Fortnight View
        grid_cols = 7
        grid_rows = 2
        dot_radius = 45 
        dot_spacing = 50
        
    else: # Year (Default)
        start_date = datetime.date(current_year, 1, 1)
        end_date = datetime.date(current_year, 12, 31)
    
    total_days = (end_date - start_date).days + 1
    
    # Days passed in THIS period
    days_passed = (now.date() - start_date).days + 1
    if days_passed < 0: days_passed = 0
    if days_passed > total_days: days_passed = total_days
    
    days_left = total_days - days_passed

    # 5. Parse Special Dates
    special_date_objects = []
    if dates_param:
        date_strings = dates_param.split(',')
        for d_str in date_strings:
            try:
                parts = d_str.strip().split('-')
                if len(parts) == 2:
                    m, d = int(parts[0]), int(parts[1])
                    try:
                        date_obj = datetime.date(current_year, m, d)
                        special_date_objects.append(date_obj)
                    except ValueError: pass
            except ValueError: pass

    # 6. Generate Image
    img = Image.new('RGB', (IMAGE_WIDTH, IMAGE_HEIGHT), color=palette['BG'])
    draw = ImageDraw.Draw(img)
    
    # Fonts
    try:
        font_small = ImageFont.truetype(FONT_PATH, 40)
    except:
        font_small = ImageFont.load_default()

    try:
        font_signature = ImageFont.truetype(FONT_SIGNATURE_PATH, 55)
    except:
        font_signature = font_small

    # --- Draw Grid ---
    DOT_SPACING = dot_spacing
    total_grid_w = (grid_cols * (dot_radius * 2)) + ((grid_cols - 1) * DOT_SPACING)
    total_grid_h = (grid_rows * (dot_radius * 2)) + ((grid_rows - 1) * DOT_SPACING)
    
    start_x = (IMAGE_WIDTH - total_grid_w) // 2
    
    # VERTICAL ALIGNMENT FIX
    if mode_param == 'year':
        # Shift DOWN for the tall year grid to avoid the clock
        start_y = (IMAGE_HEIGHT // 2) - (total_grid_h // 2) + 150 
    else:
        # True Center for smaller grids (Month, Quarter, Fortnight)
        start_y = (IMAGE_HEIGHT // 2) - (total_grid_h // 2)
    
    if start_y < 200: start_y = 200

    current_iter_date = start_date
    
    for row in range(grid_rows):
        for col in range(grid_cols):
            if current_iter_date > end_date:
                break
            
            # Color Logic
            if current_iter_date in special_date_objects:
                color = palette['SPECIAL']
            elif current_iter_date == now.date():
                color = palette['ACTIVE']
            elif current_iter_date < now.date():
                color = palette['PASSED']
            else:
                color = palette['INACTIVE']

            x = start_x + col * (dot_radius * 2 + DOT_SPACING)
            y = start_y + row * (dot_radius * 2 + DOT_SPACING)
            draw.ellipse((x, y, x + dot_radius * 2, y + dot_radius * 2), fill=color)
            
            current_iter_date += datetime.timedelta(days=1)

    # --- Draw Bottom Info ---
    range_text = "year"
    if mode_param == 'month': range_text = now.strftime("%b")
    elif mode_param == 'quarter': range_text = f"Q{(now.month-1)//3 + 1}"
    elif mode_param == 'fortnight': range_text = "period"
    
    bottom_text = f"{days_left}d left in {range_text}"
    
    bbox_text = draw.textbbox((0, 0), bottom_text, font=font_small)
    text_width = bbox_text[2] - bbox_text[0]
    text_x = (IMAGE_WIDTH - text_width) / 2
    text_y = start_y + total_grid_h + 80
    draw.text((text_x, text_y), bottom_text, font=font_small, fill=palette['ACTIVE'])

    # --- Draw Progress Bar ---
    BAR_TOTAL_WIDTH = 600
    
    if total_days > 0:
        progress_ratio = days_passed / total_days
    else:
        progress_ratio = 0

    bar_start_x = (IMAGE_WIDTH - BAR_TOTAL_WIDTH) / 2
    bar_start_y = text_y + 60 

    if bar_style_param == 'solid':
        BAR_HEIGHT = 20
        # Background
        draw.rounded_rectangle(
            (bar_start_x, bar_start_y, bar_start_x + BAR_TOTAL_WIDTH, bar_start_y + BAR_HEIGHT),
            radius=10, fill=palette['INACTIVE']
        )
        # Foreground
        fill_width = int(BAR_TOTAL_WIDTH * progress_ratio)
        if fill_width > 0:
            draw.rounded_rectangle(
                (bar_start_x, bar_start_y, bar_start_x + fill_width, bar_start_y + BAR_HEIGHT),
                radius=10, fill=palette['ACTIVE']
            )

    elif bar_style_param == 'minimal':
        BAR_HEIGHT = 6
        # Background
        draw.rounded_rectangle(
            (bar_start_x, bar_start_y, bar_start_x + BAR_TOTAL_WIDTH, bar_start_y + BAR_HEIGHT),
            radius=3, fill=palette['INACTIVE']
        )
        # Foreground
        fill_width = int(BAR_TOTAL_WIDTH * progress_ratio)
        if fill_width > 0:
            draw.rounded_rectangle(
                (bar_start_x, bar_start_y, bar_start_x + fill_width, bar_start_y + BAR_HEIGHT),
                radius=3, fill=palette['ACTIVE']
            )

    else: # Segmented (Default)
        BAR_HEIGHT = 20
        BAR_BLOCKS = 10
        BLOCK_GAP = 12
        single_block_width = (BAR_TOTAL_WIDTH - ((BAR_BLOCKS - 1) * BLOCK_GAP)) / BAR_BLOCKS
        filled_blocks = int(progress_ratio * BAR_BLOCKS)
        if days_passed > 0 and filled_blocks == 0: filled_blocks = 1

        for i in range(BAR_BLOCKS):
            b_x1 = bar_start_x + i * (single_block_width + BLOCK_GAP)
            b_y1 = bar_start_y
            b_x2 = b_x1 + single_block_width
            b_y2 = bar_start_y + BAR_HEIGHT
            color = palette['ACTIVE'] if i < filled_blocks else palette['INACTIVE']
            draw.rounded_rectangle((b_x1, b_y1, b_x2, b_y2), radius=8, fill=color)

    # --- Draw Signature ---
    if signature_param:
        bbox_sig = draw.textbbox((0, 0), signature_param, font=font_signature)
        sig_width = bbox_sig[2] - bbox_sig[0]
        sig_x = (IMAGE_WIDTH - sig_width) / 2
        sig_y = bar_start_y + BAR_HEIGHT + 80 
        draw.text((sig_x, sig_y), signature_param, font=font_signature, fill=palette['TEXT'])

    # 6. Return Image
    img_io = io.BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')