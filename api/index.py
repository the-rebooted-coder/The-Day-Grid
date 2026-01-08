from flask import Flask, send_file, request, make_response
import datetime
import calendar
from PIL import Image, ImageDraw, ImageFont
import io
import os

app = Flask(__name__)

# --- Configuration ---
IMAGE_WIDTH = 1170
IMAGE_HEIGHT = 2532
BG_COLOR = (28, 28, 30)
DOT_COLOR_ACTIVE = (255, 105, 60)
DOT_COLOR_PASSED = (255, 255, 255)
DOT_COLOR_INACTIVE = (68, 68, 70)
DOT_COLOR_SPECIAL = (255, 215, 0)
GRID_COLS = 15
GRID_ROWS = 25
DOT_RADIUS = 18
DOT_PADDING = 15

# Font Path (Includes fallback if font is missing)
FONT_PATH = os.path.join(os.path.dirname(__file__), 'fonts/Roboto-Regular.ttf')

# --- THE DASHBOARD (Embedded directly to prevent file errors) ---
HTML_DASHBOARD = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>The Grid Generator</title>
    <style>
        body { background: #1c1c1e; color: white; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; margin: 0; }
        h1 { font-weight: 900; letter-spacing: -1px; margin-bottom: 10px; font-size: 2.5rem; }
        p { color: #888; max-width: 320px; text-align: center; margin-bottom: 30px; line-height: 1.5; }
        input { background: #2c2c2e; border: 1px solid #444; padding: 15px; border-radius: 12px; color: white; width: 300px; font-size: 16px; margin-bottom: 20px; outline: none; transition: border 0.2s; }
        input:focus { border-color: #ff693c; }
        button { background: #ff693c; color: white; border: none; padding: 15px 30px; border-radius: 12px; font-weight: bold; font-size: 16px; cursor: pointer; width: 330px; transition: opacity 0.2s; }
        button:hover { opacity: 0.9; }
        .result { margin-top: 30px; display: none; text-align: center; animation: fadeIn 0.5s ease; }
        .url-box { background: #000; padding: 15px; border-radius: 8px; font-family: monospace; font-size: 13px; color: #ff693c; word-break: break-all; max-width: 300px; margin: 10px auto; border: 1px solid #333; }
        a { color: #ff693c; text-decoration: none; font-weight: 600; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
    </style>
</head>
<body>
    <h1>The Grid.</h1>
    <p>Visualize your year. Enter your special dates (MM-DD) separated by commas.</p>
    
    <input type="text" id="dates" placeholder="e.g. 03-02, 12-25">
    <button onclick="generate()">Generate Link</button>

    <div class="result" id="result">
        <p style="margin-bottom: 10px;">Copy this URL into your Shortcut:</p>
        <div class="url-box" id="urlBox"></div>
        <br>
        <a id="previewLink" href="#" target="_blank">Preview Wallpaper →</a>
    </div>

    <script>
        function generate() {
            const val = document.getElementById('dates').value;
            const baseUrl = window.location.origin + "/api/image";
            const fullUrl = baseUrl + "?dates=" + val;
            
            document.getElementById('urlBox').innerText = fullUrl;
            document.getElementById('previewLink').href = fullUrl;
            document.getElementById('result').style.display = "block";
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    # Return the HTML string directly. Indestructible.
    return HTML_DASHBOARD

@app.route('/api/image')
def generate_grid():
    # 1. Get Dates
    dates_param = request.args.get('dates', '')
    
    # 2. Setup Time (IST)
    ist_offset = datetime.timedelta(hours=5, minutes=30)
    now = datetime.datetime.now(datetime.timezone.utc) + ist_offset
    current_year = now.year
    is_leap = calendar.isleap(current_year)
    total_days_in_year = 366 if is_leap else 365
    current_day_of_year = now.timetuple().tm_yday
    days_left = total_days_in_year - current_day_of_year

    # 3. Parse Special Dates
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

    # 4. Generate Image
    img = Image.new('RGB', (IMAGE_WIDTH, IMAGE_HEIGHT), color=BG_COLOR)
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

            if dot_count in special_days_indices: color = DOT_COLOR_SPECIAL
            elif dot_count == current_day_of_year: color = DOT_COLOR_ACTIVE
            elif dot_count < current_day_of_year: color = DOT_COLOR_PASSED
            else: color = DOT_COLOR_INACTIVE

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
    draw.text((text_x, text_y), bottom_text, font=font_small, fill=DOT_COLOR_ACTIVE)

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
        color = DOT_COLOR_ACTIVE if i < filled_blocks else DOT_COLOR_INACTIVE
        draw.rounded_rectangle((b_x1, b_y1, b_x2, b_y2), radius=8, fill=color)

    # 5. Return Image
    img_io = io.BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')