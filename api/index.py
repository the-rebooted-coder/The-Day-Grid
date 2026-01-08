from flask import Flask, send_file, request, make_response
import datetime
import calendar
from PIL import Image, ImageDraw, ImageFont
import io
import os

app = Flask(__name__)

# --- Configuration & Themes ---
IMAGE_WIDTH = 1170
IMAGE_HEIGHT = 2532
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

# Font Path
FONT_PATH = os.path.join(os.path.dirname(__file__), 'fonts/Roboto-Regular.ttf')

# --- THE DASHBOARD (Updated with Theme Toggle & Copy Button) ---
HTML_DASHBOARD = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>The Grid Generator</title>
    <style>
        body { background: #1c1c1e; color: white; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 100vh; margin: 0; padding: 20px; box-sizing: border-box; }
        h1 { font-weight: 900; letter-spacing: -1px; margin-bottom: 10px; font-size: 2.5rem; }
        p { color: #888; max-width: 320px; text-align: center; margin-bottom: 30px; line-height: 1.5; }
        
        /* Inputs */
        .input-group { width: 100%; max-width: 330px; margin-bottom: 20px; }
        input[type="text"] { background: #2c2c2e; border: 1px solid #444; padding: 15px; border-radius: 12px; color: white; width: 100%; font-size: 16px; outline: none; transition: border 0.2s; box-sizing: border-box; }
        input[type="text"]:focus { border-color: #ff693c; }
        
        /* Theme Toggle */
        .theme-switch { display: flex; gap: 10px; margin-bottom: 25px; background: #2c2c2e; padding: 5px; border-radius: 12px; width: 100%; max-width: 330px; box-sizing: border-box; }
        .theme-option { flex: 1; text-align: center; padding: 10px; border-radius: 8px; cursor: pointer; font-weight: 600; font-size: 14px; color: #888; transition: all 0.2s; }
        .theme-option.active { background: #444; color: white; }
        input[type="radio"] { display: none; }

        /* Buttons */
        button.generate-btn { background: #ff693c; color: white; border: none; padding: 15px 30px; border-radius: 12px; font-weight: bold; font-size: 16px; cursor: pointer; width: 100%; max-width: 330px; transition: opacity 0.2s; }
        button.generate-btn:hover { opacity: 0.9; }

        /* Result Area */
        .result { margin-top: 30px; display: none; text-align: center; animation: fadeIn 0.5s ease; width: 100%; max-width: 330px; }
        
        .url-container { display: flex; gap: 10px; margin: 10px 0; }
        .url-box { background: #000; padding: 12px; border-radius: 8px; font-family: monospace; font-size: 13px; color: #ff693c; border: 1px solid #333; flex-grow: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        
        .copy-btn { background: #333; border: 1px solid #444; border-radius: 8px; cursor: pointer; color: white; padding: 0 15px; font-weight: bold; transition: background 0.2s; }
        .copy-btn:hover { background: #444; }
        
        a { color: #ff693c; text-decoration: none; font-weight: 600; display: inline-block; margin-top: 10px; }
        
        footer { margin-top: 60px; color: #555; font-family: 'Courier New', monospace; font-size: 14px; opacity: 0.8; }
        
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
    </style>
</head>
<body>
    <h1>The Grid.</h1>
    <p>Visualize your year. Enter special dates and choose your style.</p>
    
    <div class="input-group">
        <input type="text" id="dates" placeholder="MM-DD, MM-DD (e.g. 03-02, 12-25)">
    </div>

    <div class="theme-switch">
        <label class="theme-option active" id="lbl-dark" onclick="setTheme('dark')">
            Dark Mode
            <input type="radio" name="theme" value="dark" checked>
        </label>
        <label class="theme-option" id="lbl-light" onclick="setTheme('light')">
            Light Mode
            <input type="radio" name="theme" value="light">
        </label>
    </div>

    <button class="generate-btn" onclick="generate()">Generate Link</button>

    <div class="result" id="result">
        <p style="margin-bottom: 5px; font-size: 0.9rem;">Your automation URL:</p>
        
        <div class="url-container">
            <div class="url-box" id="urlBox"></div>
            <button class="copy-btn" onclick="copyToClipboard()">Copy</button>
        </div>
        
        <a id="previewLink" href="#" target="_blank">Preview Wallpaper →</a>
    </div>

    <footer>&lt;/&gt; with ❤️ by Spandan.</footer>

    <script>
        let selectedTheme = 'dark';

        function setTheme(theme) {
            selectedTheme = theme;
            document.getElementById('lbl-dark').className = theme === 'dark' ? 'theme-option active' : 'theme-option';
            document.getElementById('lbl-light').className = theme === 'light' ? 'theme-option active' : 'theme-option';
        }

        function generate() {
            const val = document.getElementById('dates').value;
            const baseUrl = window.location.origin + "/api/image";
            
            // Build URL parameters
            const params = new URLSearchParams();
            if (val) params.append('dates', val);
            params.append('theme', selectedTheme);
            
            const fullUrl = baseUrl + "?" + params.toString();
            
            document.getElementById('urlBox').innerText = fullUrl;
            document.getElementById('previewLink').href = fullUrl;
            document.getElementById('result').style.display = "block";
        }

        function copyToClipboard() {
            const text = document.getElementById('urlBox').innerText;
            navigator.clipboard.writeText(text).then(() => {
                const btn = document.querySelector('.copy-btn');
                const originalText = btn.innerText;
                btn.innerText = "Copied!";
                btn.style.background = "#ff693c";
                setTimeout(() => {
                    btn.innerText = originalText;
                    btn.style.background = "#333";
                }, 2000);
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
    theme_param = request.args.get('theme', 'dark') # Default to dark

    # 2. Select Theme Colors
    palette = THEMES.get(theme_param, THEMES['dark'])
    
    # 3. Setup Time (IST)
    ist_offset = datetime.timedelta(hours=5, minutes=30)
    now = datetime.datetime.now(datetime.timezone.utc) + ist_offset
    current_year = now.year
    is_leap = calendar.isleap(current_year)
    total_days_in_year = 366 if is_leap else 365
    current_day_of_year = now.timetuple().tm_yday
    days_left = total_days_in_year - current_day_of_year

    # 4. Parse Special Dates
    special_days_indices = []
    if dates_param:
        date_strings = dates_param.split(',')
        for d_str in date_strings:
            try:
                parts = d_str.strip().split('-')
                if len(parts) == 2:
                    m, d = int(parts[0]), int(parts[1])
                    try:
                        date_obj = datetime.date(current_year, m, d)
                        special_days_indices.append(date_obj.timetuple().tm_yday)
                    except ValueError: pass
            except ValueError: pass

    # 5. Generate Image
    img = Image.new('RGB', (IMAGE_WIDTH, IMAGE_HEIGHT), color=palette['BG'])
    draw = ImageDraw.Draw(img)
    
    try:
        font_small = ImageFont.truetype(FONT_PATH, 40)
    except:
        font_small = ImageFont.load_default()

    # --- Draw Grid ---
    total_grid_width = (GRID_COLS * (DOT_RADIUS * 2)) + ((GRID_COLS - 1) * DOT_PADDING)
    total_grid_height = (GRID_ROWS * (DOT_RADIUS * 2)) + ((GRID_ROWS - 1) * DOT_PADDING)
    start_x = (IMAGE_WIDTH - total_grid_width) // 2
    start_y = (IMAGE_HEIGHT - total_grid_height) // 2 + 60

    dot_count = 0
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            dot_count += 1
            if dot_count > total_days_in_year: break

            if dot_count in special_days_indices: color = palette['SPECIAL']
            elif dot_count == current_day_of_year: color = palette['ACTIVE']
            elif dot_count < current_day_of_year: color = palette['PASSED']
            else: color = palette['INACTIVE']

            x = start_x + col * (DOT_RADIUS * 2 + DOT_PADDING)
            y = start_y + row * (DOT_RADIUS * 2 + DOT_PADDING)
            draw.ellipse((x, y, x + DOT_RADIUS * 2, y + DOT_RADIUS * 2), fill=color)

    # --- Draw Bottom Info ---
    grid_bottom_y = start_y + total_grid_height
    bottom_text = f"{days_left}d left"
    bbox_text = draw.textbbox((0, 0), bottom_text, font=font_small)
    text_width = bbox_text[2] - bbox_text[0]
    text_x = (IMAGE_WIDTH - text_width) / 2
    text_y = grid_bottom_y + 50
    draw.text((text_x, text_y), bottom_text, font=font_small, fill=palette['ACTIVE'])

    # --- Draw Progress Bar ---
    BAR_TOTAL_WIDTH = 600   
    BAR_HEIGHT = 20         
    BAR_BLOCKS = 10         
    BLOCK_GAP = 12          
    total_gap_width = (BAR_BLOCKS - 1) * BLOCK_GAP
    single_block_width = (BAR_TOTAL_WIDTH - total_gap_width) / BAR_BLOCKS
    progress_ratio = current_day_of_year / total_days_in_year
    filled_blocks = int(progress_ratio * BAR_BLOCKS)
    if current_day_of_year > 0 and filled_blocks == 0: filled_blocks = 1

    bar_start_x = (IMAGE_WIDTH - BAR_TOTAL_WIDTH) / 2
    bar_start_y = text_y + 60 

    for i in range(BAR_BLOCKS):
        b_x1 = bar_start_x + i * (single_block_width + BLOCK_GAP)
        b_y1 = bar_start_y
        b_x2 = b_x1 + single_block_width
        b_y2 = bar_start_y + BAR_HEIGHT
        color = palette['ACTIVE'] if i < filled_blocks else palette['INACTIVE']
        draw.rounded_rectangle((b_x1, b_y1, b_x2, b_y2), radius=8, fill=color)

    # 6. Return Image
    img_io = io.BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')