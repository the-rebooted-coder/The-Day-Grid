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

# --- THE DASHBOARD (Dbrand Tone + Shortcut Link) ---
HTML_DASHBOARD = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>The Grid Generator</title>
    
    <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><circle cx=%2250%22 cy=%2250%22 r=%2250%22 fill=%22%23ff693c%22/></svg>">
    <link rel="apple-touch-icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><rect width=%22100%22 height=%22100%22 fill=%22%231c1c1e%22/><circle cx=%2250%22 cy=%2250%22 r=%2240%22 fill=%22%23ff693c%22/></svg>">

    <style>
        body { background: #1c1c1e; color: white; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 100vh; margin: 0; padding: 40px 20px; box-sizing: border-box; }
        h1 { font-weight: 900; letter-spacing: -1px; margin-bottom: 5px; font-size: 2.5rem; text-align: center; }
        
        .subtitle-container { display: flex; align-items: center; justify-content: center; gap: 8px; margin-bottom: 30px; }
        p.subtitle { color: #888; text-align: center; line-height: 1.5; font-size: 0.95rem; margin: 0; }
        
        /* Info Button */
        .info-btn { background: none; border: 1px solid #444; color: #888; border-radius: 50%; width: 20px; height: 20px; font-size: 12px; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.2s; font-family: serif; font-weight: bold; }
        .info-btn:hover { border-color: #ff693c; color: #ff693c; }

        /* Section Headers */
        h2 { font-size: 0.9rem; text-transform: uppercase; letter-spacing: 1px; color: #666; margin: 20px 0 10px 0; width: 100%; max-width: 330px; text-align: left; border-bottom: 1px solid #333; padding-bottom: 5px; }

        /* Dynamic Date List */
        #date-list { width: 100%; max-width: 330px; display: flex; flex-direction: column; gap: 10px; margin-bottom: 15px; }
        .date-row { display: flex; gap: 10px; align-items: center; animation: fadeIn 0.3s ease; }
        
        /* Date Inputs */
        input[type="date"] { background: #2c2c2e; border: 1px solid #444; padding: 12px; border-radius: 12px; color: white; flex-grow: 1; font-family: inherit; font-size: 16px; outline: none; transition: border 0.2s; color-scheme: dark; }
        input[type="date"]:focus { border-color: #ff693c; }
        
        /* Buttons */
        .btn-icon { background: #333; border: 1px solid #444; width: 44px; height: 44px; border-radius: 12px; display: flex; align-items: center; justify-content: center; cursor: pointer; color: #ff693c; font-size: 20px; transition: background 0.2s; flex-shrink: 0; }
        .btn-icon:hover { background: #444; }
        .btn-remove { color: #ff453a; }

        .btn-add { background: transparent; border: 1px dashed #444; color: #888; width: 100%; max-width: 330px; padding: 12px; border-radius: 12px; cursor: pointer; font-size: 14px; margin-bottom: 10px; transition: all 0.2s; }
        .btn-add:hover { border-color: #ff693c; color: #ff693c; background: rgba(255, 105, 60, 0.1); }

        /* Theme Toggle */
        .theme-switch { display: flex; gap: 10px; background: #2c2c2e; padding: 5px; border-radius: 12px; width: 100%; max-width: 330px; box-sizing: border-box; }
        .theme-option { flex: 1; text-align: center; padding: 10px; border-radius: 8px; cursor: pointer; font-weight: 600; font-size: 14px; color: #888; transition: all 0.2s; }
        .theme-option.active { background: #444; color: white; }
        input[type="radio"] { display: none; }

        /* Generate Button */
        button.generate-btn { background: #ff693c; color: white; border: none; padding: 15px 30px; border-radius: 12px; font-weight: bold; font-size: 16px; cursor: pointer; width: 100%; max-width: 330px; margin-top: 30px; transition: opacity 0.2s; box-shadow: 0 4px 15px rgba(255, 105, 60, 0.3); }
        button.generate-btn:hover { opacity: 0.9; }

        /* Result Area */
        .result { margin-top: 30px; display: none; text-align: center; animation: slideUp 0.5s ease; width: 100%; max-width: 330px; border-top: 1px solid #333; padding-top: 20px; }
        .url-container { display: flex; gap: 10px; margin: 10px 0; }
        .url-box { background: #000; padding: 12px; border-radius: 8px; font-family: monospace; font-size: 13px; color: #ff693c; border: 1px solid #333; flex-grow: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .copy-btn { background: #333; border: 1px solid #444; border-radius: 8px; cursor: pointer; color: white; padding: 0 15px; font-weight: bold; transition: background 0.2s; }
        .copy-btn:hover { background: #444; }
        
        /* Shortcut Section */
        .shortcut-section { margin-top: 25px; background: #2c2c2e; padding: 20px; border-radius: 12px; border: 1px solid #444; }
        .shortcut-btn { background: white; color: black; display: block; width: 100%; padding: 12px; border-radius: 8px; font-weight: bold; text-decoration: none; margin-top: 10px; box-sizing: border-box; }
        .shortcut-btn:hover { background: #e0e0e0; opacity: 1; }

        a.preview-link { color: #ff693c; text-decoration: none; font-weight: 600; display: inline-block; margin-top: 10px; font-size: 0.9rem; }
        
        footer { margin-top: 60px; color: #555; font-family: 'Courier New', monospace; font-size: 13px; opacity: 0.8; }
        
        /* MODAL STYLES */
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
        .close-modal:hover { background: #444; }

        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
        @keyframes slideUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
    </style>
</head>
<body>
    <h1>The Grid.</h1>
    
    <div class="subtitle-container">
        <p class="subtitle">Visualize your year.<br>Add your special dates below.</p>
        <button class="info-btn" onclick="openModal()" title="What do the colors mean?">i</button>
    </div>
    
    <div id="date-list">
        <div class="date-row">
            <input type="date" class="date-input">
            <button class="btn-icon btn-remove" onclick="removeDate(this)" title="Remove">×</button>
        </div>
    </div>
    <button class="btn-add" onclick="addDate()">+ Add another date</button>

    <h2>Theme</h2>
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
        <p style="margin-bottom: 5px; font-size: 0.9rem; color: #888;">Step 1: Copy this URL.</p>
        
        <div class="url-container">
            <div class="url-box" id="urlBox"></div>
            <button class="copy-btn" onclick="copyToClipboard()">Copy</button>
        </div>
        
        <a class="preview-link" id="previewLink" href="#" target="_blank">Preview Wallpaper →</a>

        <div class="shortcut-section">
            <p style="margin: 0 0 10px 0; font-size: 0.9rem; color: #ccc;">Step 2: Install the Shortcut.</p>
            <p style="margin: 0 0 10px 0; font-size: 0.8rem; color: #888; line-height: 1.4;">
                Since you probably need hand-holding: Install the shortcut, paste the URL when asked, and stop wasting time. The rest is automatic.
            </p>
            <a href="https://www.icloud.com/shortcuts/99a190f4001844f9ade585fc8eafd47e" class="shortcut-btn" target="_blank">Install iOS Shortcut</a>
        </div>
    </div>

    <footer>&lt;/&gt; with ❤️ by Spandan.</footer>

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
        let selectedTheme = 'dark';

        // Modal Logic
        function openModal() { toggleModal(true); }
        function closeModal(e) { if(e.target === document.getElementById('modalOverlay')) toggleModal(false); }
        
        function toggleModal(show) {
            const overlay = document.getElementById('modalOverlay');
            const modal = overlay.querySelector('.modal');
            
            if (show) {
                overlay.style.display = 'flex';
                // Trigger reflow
                void overlay.offsetWidth;
                overlay.style.opacity = '1';
                modal.style.transform = 'scale(1)';
            } else {
                overlay.style.opacity = '0';
                modal.style.transform = 'scale(0.9)';
                setTimeout(() => { overlay.style.display = 'none'; }, 300);
            }
        }

        // Add a new date input row
        function addDate() {
            const container = document.getElementById('date-list');
            const div = document.createElement('div');
            div.className = 'date-row';
            div.innerHTML = `
                <input type="date" class="date-input">
                <button class="btn-icon btn-remove" onclick="removeDate(this)">×</button>
            `;
            container.appendChild(div);
        }

        // Remove a date input row
        function removeDate(btn) {
            const container = document.getElementById('date-list');
            if (container.children.length > 1) {
                btn.parentElement.remove();
            } else {
                btn.parentElement.querySelector('input').value = '';
            }
        }

        function setTheme(theme) {
            selectedTheme = theme;
            document.getElementById('lbl-dark').className = theme === 'dark' ? 'theme-option active' : 'theme-option';
            document.getElementById('lbl-light').className = theme === 'light' ? 'theme-option active' : 'theme-option';
        }

        function generate() {
            const inputs = document.querySelectorAll('.date-input');
            let dateArray = [];

            inputs.forEach(input => {
                if (input.value) {
                    const parts = input.value.split('-'); 
                    if (parts.length === 3) {
                        dateArray.push(`${parts[1]}-${parts[2]}`);
                    }
                }
            });

            const val = dateArray.join(',');
            const baseUrl = window.location.origin + "/api/image";
            
            const params = new URLSearchParams();
            if (val) params.append('dates', val);
            params.append('theme', selectedTheme);
            
            const fullUrl = baseUrl + "?" + params.toString();
            
            document.getElementById('urlBox').innerText = fullUrl;
            document.getElementById('previewLink').href = fullUrl;
            document.getElementById('result').style.display = "block";
            
            document.getElementById('result').scrollIntoView({ behavior: 'smooth' });
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
    theme_param = request.args.get('theme', 'dark')

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