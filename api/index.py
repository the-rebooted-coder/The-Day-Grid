from flask import Flask, send_file, request, send_from_directory
import datetime
import calendar
from PIL import Image, ImageDraw, ImageFont
import io
import os
import urllib.request
import json

app = Flask(__name__)

# --- Configuration & Themes ---
# Dimensions are dynamic based on request
MOBILE_WIDTH = 1170
MOBILE_HEIGHT = 2532
DESKTOP_WIDTH = 2560
DESKTOP_HEIGHT = 1440

# Default Settings
DOT_RADIUS = 18
DOT_PADDING = 15

# Define Color Palettes
THEMES = {
    'dark': {
        'BG': (28, 28, 30),
        'ACTIVE': (255, 105, 60),    # Orange
        'PASSED': (255, 255, 255),   # White
        'INACTIVE': (68, 68, 70),    # Dim Gray
        'WEEKEND': (44, 44, 46),     # Darker Gray for Weekends
        'SPECIAL': (255, 215, 0),    # Gold
        'TEXT': (255, 255, 255)      # White Text
    },
    'light': {
        'BG': (242, 242, 247),       # iOS Light Gray
        'ACTIVE': (255, 105, 60),    # Orange
        'PASSED': (60, 60, 67),      # Dark Gray (Completed)
        'INACTIVE': (209, 209, 214), # Light Gray (Future)
        'WEEKEND': (229, 229, 234),  # Slightly different gray
        'SPECIAL': (255, 204, 0),    # Gold
        'TEXT': (0, 0, 0)            # Black Text
    }
}

# Font Paths
FONT_DIR = os.path.join(os.path.dirname(__file__), 'fonts')
FONT_PATH = os.path.join(FONT_DIR, 'Roboto-Regular.ttf')
FONT_SIGNATURE_PATH = os.path.join(FONT_DIR, 'Buffalo.otf')

# --- Helper: Fetch Emoji Image ---
emoji_cache = {}

def get_emoji_image(emoji_char):
    """Downloads the PNG representation of an emoji from Twemoji CDN."""
    if emoji_char in emoji_cache:
        return emoji_cache[emoji_char]
    
    try:
        # Get hex codepoint (e.g. 🍰 -> 1f382)
        codepoint = "-".join([f"{ord(c):x}" for c in emoji_char if ord(c) != 0xfe0f])
        
        url = f"https://cdnjs.cloudflare.com/ajax/libs/twemoji/14.0.2/72x72/{codepoint}.png"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        
        with urllib.request.urlopen(req) as response:
            data = response.read()
            img = Image.open(io.BytesIO(data)).convert("RGBA")
            emoji_cache[emoji_char] = img
            return img
    except Exception as e:
        print(f"Failed to download emoji {emoji_char}: {e}")
        return None

# --- THE DASHBOARD ---
HTML_DASHBOARD = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>The Grid Generator</title>
    <meta name="description" content="Visualize your year. A minimal wallpaper generator for iOS and Desktop.">

    <meta property="og:type" content="website">
    <meta property="og:url" content="https://the-day-grid.vercel.app/">
    <meta property="og:title" content="The Grid.">
    <meta property="og:description" content="Visualize your year. Don't waste it.">
    <meta property="og:image" content="https://the-day-grid.vercel.app/api/image?theme=dark&mode=year&bar_style=segmented">

    <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><circle cx=%2250%22 cy=%2250%22 r=%2250%22 fill=%22%23ff693c%22/></svg>">
    <link rel="apple-touch-icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><rect width=%22100%22 height=%22100%22 fill=%22%231c1c1e%22/><circle cx=%2250%22 cy=%2250%22 r=%2240%22 fill=%22%23ff693c%22/></svg>">

    <script defer src="/_vercel/insights/script.js"></script>

    <style>
        /* Load Custom Font for Live Preview */
        @font-face {
            font-family: 'SignatureFont';
            src: url('/fonts/Buffalo.otf');
        }

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
        h1 { font-weight: 900; letter-spacing: -1px; margin: 0 0 5px 0; font-size: 2.5rem; display: flex; align-items: center; justify-content: center; gap: 8px; }
        
        #animated-title {
            transition: width 0.4s cubic-bezier(0.25, 0.8, 0.25, 1), opacity 0.2s ease-in-out;
            opacity: 1;
            display: inline-flex;
            justify-content: center;
            align-items: center;
            vertical-align: middle;
            overflow: hidden;
            white-space: nowrap;
            height: 40px;
            cursor: pointer;
        }
        
        #ruler {
            visibility: hidden;
            position: absolute;
            white-space: nowrap;
            font-weight: 900;
            font-size: 2.5rem; 
            letter-spacing: -1px;
            pointer-events: none;
        }

        .title-dot { width: 28px; height: 28px; border-radius: 50%; display: inline-block; flex-shrink: 0; }
        
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
        .date-row { display: flex; gap: 8px; align-items: center; }
        
        .date-picker-group { display: flex; flex-grow: 1; gap: 5px; }
        select { background: #2c2c2e; border: 1px solid #444; padding: 10px; border-radius: 8px; color: white; font-family: inherit; font-size: 14px; outline: none; transition: border 0.2s; color-scheme: dark; box-sizing: border-box; }
        select:focus, input[type="text"]:focus { border-color: #ff693c; }
        .month-select { flex: 2; }
        .day-select { flex: 1; }

        .emoji-select { flex-grow: 0 !important; width: 60px !important; font-size: 18px !important; appearance: none; -webkit-appearance: none; cursor: pointer; padding: 10px 0; text-align: center; text-align-last: center; -moz-text-align-last: center; }

        input[type="text"] { background: #2c2c2e; border: 1px solid #444; padding: 10px; border-radius: 8px; color: white; flex-grow: 1; font-family: inherit; font-size: 14px; outline: none; transition: border 0.2s; width: 100%; box-sizing: border-box; }
        
        #signature { font-family: 'SignatureFont', cursive; font-size: 28px; padding: 12px 10px; letter-spacing: 1px; }
        #signature::placeholder { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 14px; letter-spacing: normal; opacity: 0.5; padding-top: 5px; }

        /* Toggle Switch CSS */
        .toggle-container { display: flex; align-items: center; justify-content: space-between; background: #2c2c2e; padding: 12px; border-radius: 8px; border: 1px solid #444; margin-bottom: 20px; }
        .toggle-label { font-size: 14px; font-weight: 500; }
        .switch { position: relative; display: inline-block; width: 44px; height: 24px; }
        .switch input { opacity: 0; width: 0; height: 0; }
        .slider { position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: #444; -webkit-transition: .4s; transition: .4s; border-radius: 24px; }
        .slider:before { position: absolute; content: ""; height: 20px; width: 20px; left: 2px; bottom: 2px; background-color: white; -webkit-transition: .4s; transition: .4s; border-radius: 50%; }
        input:checked + .slider { background-color: #ff693c; }
        input:checked + .slider:before { transform: translateX(20px); }

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
        
        /* PREVIEW FRAME CSS */
        .preview-frame {
            background: #000;
            margin: 20px auto;
            overflow: hidden;
            box-shadow: 0 20px 40px rgba(0,0,0,0.6);
            transition: all 0.3s ease;
            position: relative;
        }

        /* IPHONE STYLE */
        .preview-frame.mobile {
            width: 280px;
            aspect-ratio: 9 / 19.5;
            border-radius: 40px;
            border: 8px solid #2b2b2b;
        }
        
        .preview-frame.mobile.dynamic-island .dynamic-island {
            width: 80px;
            height: 24px;
            background: #000;
            position: absolute;
            top: 12px;
            left: 50%;
            transform: translateX(-50%);
            border-radius: 20px;
            z-index: 10;
            display: block;
        }

        .preview-frame.mobile.notch .dynamic-island {
            width: 140px;
            height: 28px;
            background: #000;
            position: absolute;
            top: 0;
            left: 50%;
            transform: translateX(-50%);
            border-bottom-left-radius: 16px;
            border-bottom-right-radius: 16px;
            border-radius: 0 0 16px 16px;
            z-index: 10;
            display: block;
        }

        /* DESKTOP STYLE */
        .preview-frame.desktop {
            width: 300px;
            aspect-ratio: 16 / 9;
            border-radius: 8px;
            border: 8px solid #2b2b2b;
            border-bottom-width: 12px; /* Thicker chin for monitor */
        }
        
        .preview-frame.desktop .dynamic-island { display: none; }

        .mockup-img { width: 100%; height: 100%; object-fit: cover; display: block; }

        .shortcut-section { margin-top: 20px; background: #2c2c2e; padding: 15px; border-radius: 12px; border: 1px solid #444; }
        .shortcut-btn { background: white; color: black; display: block; width: 100%; padding: 12px; border-radius: 8px; font-weight: bold; text-decoration: none; margin-top: 10px; box-sizing: border-box; }
        
        footer { margin-top: auto; color: #555; font-family: 'Courier New', monospace; font-size: 13px; opacity: 0.8; padding-bottom: 10px; width: 100%; text-align: center; }
        
        .footer-link { color: #555; text-decoration: none; border-bottom: 1px dotted #555; transition: color 0.2s; cursor: pointer; font-size: 11px; margin-top: 5px; display: inline-block; }
        .footer-link:hover { color: #ff693c; border-color: #ff693c; }
        
        .labs-product { font-size: 10px; color: #555; margin-top: 8px; font-weight: 600; letter-spacing: 0.5px; }

        .modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0, 0, 0, 0.7); backdrop-filter: blur(5px); z-index: 1000; display: none; align-items: center; justify-content: center; opacity: 0; transition: opacity 0.3s; }
        .modal { background: #1c1c1e; border: 1px solid #333; padding: 25px; border-radius: 16px; width: 90%; max-width: 320px; transform: scale(0.9); transition: transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275); box-shadow: 0 20px 50px rgba(0,0,0,0.5); max-height: 70vh; overflow-y: auto; }
        .modal h3 { margin-top: 0; color: white; text-align: center; }
        
        .color-legend { display: flex; flex-direction: column; gap: 15px; margin-top: 20px; }
        .legend-item { display: flex; align-items: center; gap: 15px; font-size: 0.95rem; color: #ccc; }
        .dot { width: 16px; height: 16px; border-radius: 50%; display: inline-block; flex-shrink: 0; }
        .dot.white { background: #fff; border: 1px solid #444; }
        .dot.orange { background: #ff693c; box-shadow: 0 0 8px rgba(255, 105, 60, 0.6); }
        .dot.yellow { background: #ffd700; box-shadow: 0 0 8px rgba(255, 215, 0, 0.6); }
        .dot.gray { background: #444446; }
        
        .close-modal { background: #333; border: none; color: white; width: 100%; padding: 12px; border-radius: 10px; margin-top: 25px; cursor: pointer; font-weight: 600; }

        /* Release Notes Styles */
        .release-list { text-align: left; padding-left: 20px; color: #ccc; font-size: 0.9rem; line-height: 1.6; margin-bottom: 25px; }
        .github-btn { display: block; background: transparent; border: 1px solid #555; color: #888; text-decoration: none; padding: 12px; border-radius: 10px; text-align: center; font-weight: 600; font-size: 14px; transition: all 0.2s; }
        .github-btn:hover { border-color: #ff693c; color: #ff693c; }

        @keyframes slideDown { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes slideUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
    </style>
</head>
<body>
    <div class="header-section">
        <span id="ruler"></span>
        <h1>The <span id="animated-title" onclick="replayAnimation()">Grid.</span></h1>
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
            <h2>Device Size</h2>
            <div style="margin-bottom: 20px;">
                <select id="device-size" style="width: 100%" onchange="updateDevicePreview()">
                    <option value="mobile">Mobile (Portrait)</option>
                    <option value="desktop">Desktop / Monitor (Landscape)</option>
                </select>
            </div>

            <h2>View Mode</h2>
            <div style="margin-bottom: 20px;">
                <select id="view-mode" style="width: 100%">
                    <option value="year">Full Year (Default)</option>
                    <option value="segregated_months">Segregated Months</option>
                    <option value="quarter">Current Quarter</option>
                    <option value="month">Current Month</option>
                    <option value="fortnight">Fortnight (14 Days)</option>
                </select>
            </div>

            <h2>Visuals</h2>
            <div class="toggle-container">
                <span class="toggle-label">Highlight Weekends</span>
                <label class="switch">
                    <input type="checkbox" id="weekend-toggle">
                    <span class="slider"></span>
                </label>
            </div>

            <h2>Progress Bar Style</h2>
            <div style="margin-bottom: 20px;">
                <select id="bar-style" style="width: 100%">
                    <option value="segmented">Segmented (Default)</option>
                    <option value="solid">Solid</option>
                    <option value="minimal">Minimal</option>
                </select>
            </div>

            <h2>Dates of Importance</h2>
            <div id="date-list">
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
            </div>

            <div id="phone-frame" class="preview-frame mobile dynamic-island">
                <div class="dynamic-island"></div>
                <img id="mockup-img" class="mockup-img" src="" alt="Preview">
            </div>

            <div class="shortcut-section">
                <p style="margin: 0 0 10px 0; font-size: 0.9rem; color: #ccc;">Step 2: Install the Shortcut.</p>
                <p style="margin: 0 0 10px 0; font-size: 0.8rem; color: #888; line-height: 1.4;">
                    For Mobile: Use Shortcuts app. <br>For Desktop: Use a script to fetch this URL daily.
                </p>
                <a href="https://www.icloud.com/shortcuts/99a190f4001844f9ade585fc8eafd47e" class="shortcut-btn" target="_blank">Install iOS Shortcut</a>
            </div>
        </div>
    </div>

    <footer>
        &lt;/&gt; with ❤️ by Spandan.<br>
        <span onclick="openReleaseModal()" class="footer-link">Version 3.2 Prod.</span>
        <div class="labs-product">An S² Labs Product 🥼</div>
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

    <div class="modal-overlay" id="releaseModalOverlay" onclick="closeReleaseModal(event)">
        <div class="modal">
            <h3>Version 3.2 Notes</h3>
            <ul class="release-list">
                <li><strong>Desktop Support:</strong> You can now generate 1440p landscape grids for your monitor. Because anxiety should follow you to work, too.</li>
                <li><strong>Emoji Chooser:</strong> Because a colored dot wasn't "aesthetic" enough for your Instagram story. Send your "thanks" to <a href="https://www.instagram.com/im.amitpatwa" target="_blank" style="color: #ff693c; text-decoration: none;">Amit</a> for the extra bloat.</li>
                <li><strong>We Killed the 'Year' Input:</strong> It's an annual calendar, Einstein. Stop trying to schedule things for 2027.</li>
                <li><strong>Goldfish Memory Patch:</strong> The app now remembers your settings and dates locally. Because apparently, typing your own name more than once is too much to ask of you.</li>
                <li><strong>Live Signature:</strong> Type your name. See it appear. It's not magic, it's JavaScript. Try not to be impressed.</li>
                <li><strong>Weekend Highlight:</strong> Visual proof that you only live for 28% of your life.</li>
                <li><strong>Segregated Months:</strong> A new view for those easily overwhelmed by 365 dots. Deep breaths.</li>
                <li><strong>Layout Fixes:</strong> Fixed the Full Year view alignment. It used to look terrible. Now it looks slightly less terrible. Thanks to <a href="https://www.linkedin.com/in/kartikeya-srivastava-b527901a4/?utm_source=share&utm_campaign=share_via&utm_content=profile&utm_medium=ios_app" target="_blank" style="color: #ff693c; text-decoration: none;">Kartikey</a> for pointing out the UI inconsistency we were praying you wouldn't notice.</li>
            </ul>
            <a href="https://github.com/the-rebooted-coder/The-Day-Grid/tree/main" target="_blank" class="github-btn">View Source on GitHub</a>
            <button class="close-modal" onclick="toggleReleaseModal(false)">Close</button>
        </div>
    </div>

    <script>
        const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
        
        function getMonthOptionsHtml(selected) {
            let html = '<option value="" disabled ' + (!selected ? 'selected' : '') + '>Month</option>';
            MONTHS.forEach((m, i) => {
                const val = i + 1;
                const isSel = val == selected ? 'selected' : '';
                html += `<option value="${val}" ${isSel}>${m}</option>`;
            });
            return html;
        }

        function getDayOptionsHtml(selected) {
            let html = '<option value="" disabled ' + (!selected ? 'selected' : '') + '>Day</option>';
            for (let i = 1; i <= 31; i++) {
                const isSel = i == selected ? 'selected' : '';
                html += `<option value="${i}" ${isSel}>${i}</option>`;
            }
            return html;
        }

        function getEmojiOptionsHtml(selected) {
            const emojis = ["🟡", "🍰", "❤️", "🚀", "💰", "✈️", "💀", "🍺"];
            let html = "";
            emojis.forEach(e => {
                const val = e === '🟡' ? '' : e;
                const isSel = val === selected ? 'selected' : '';
                html += `<option value="${val}" ${isSel}>${e}</option>`;
            });
            return html;
        }

        // --- LOCAL STORAGE LOGIC ---
        function savePreferences() {
            const prefs = {
                deviceSize: document.getElementById('device-size').value,
                viewMode: document.getElementById('view-mode').value,
                barStyle: document.getElementById('bar-style').value,
                highlightWeekends: document.getElementById('weekend-toggle').checked,
                theme: selectedTheme,
                signature: document.getElementById('signature').value,
                dates: []
            };
            
            // Collect Dates
            const rows = document.querySelectorAll('.date-row');
            rows.forEach(row => {
                const m = row.querySelector('.month-select').value;
                const d = row.querySelector('.day-select').value;
                const e = row.querySelector('.emoji-select').value;
                if(m || d || e) {
                    prefs.dates.push({m: m, d: d, e: e});
                }
            });
            
            localStorage.setItem('grid_prefs_v3', JSON.stringify(prefs));
        }

        function loadPreferences() {
            const stored = localStorage.getItem('grid_prefs_v3');
            if (!stored) {
                addDate(); // Default empty row
                return;
            }

            try {
                const prefs = JSON.parse(stored);
                
                // Set Fields
                // Note: We deliberately skip setting 'deviceSize' from local storage on load
                // to allow the auto-detector to run fresh for the current device.
                
                if(prefs.viewMode) document.getElementById('view-mode').value = prefs.viewMode;
                if(prefs.barStyle) document.getElementById('bar-style').value = prefs.barStyle;
                if(prefs.highlightWeekends !== undefined) document.getElementById('weekend-toggle').checked = prefs.highlightWeekends;
                if(prefs.theme) setTheme(prefs.theme);
                if(prefs.signature) document.getElementById('signature').value = prefs.signature;

                // Rebuild Dates
                const container = document.getElementById('date-list');
                container.innerHTML = ''; // Clear existing
                
                if (prefs.dates && prefs.dates.length > 0) {
                    prefs.dates.forEach(d => {
                        addDate(d.m, d.d, d.e);
                    });
                } else {
                    addDate();
                }

            } catch (e) {
                console.error("Failed to load prefs", e);
                addDate();
            }
        }

        // --- DEVICE DETECTION LOGIC ---
        function detectDeviceType() {
            // Check logical screen width to guess device family
            const width = window.innerWidth;
            const frame = document.getElementById('phone-frame');
            const select = document.getElementById('device-size');
            
            // If the screen is wider than a typical tablet/mobile (1000px breakpoint)
            if (width > 1000) {
                // It's a Desktop/Laptop
                select.value = 'desktop';
                updateDevicePreview();
            } else {
                // It's Mobile
                select.value = 'mobile';
                updateDevicePreview();
                
                // Fine-tune mobile frame style (Notch vs Island)
                // Heuristic based on logical width
                if (width === 393 || width === 430) {
                    frame.classList.add('dynamic-island');
                    frame.classList.remove('notch');
                } else if (width === 390 || width === 428 || width === 375 || width === 414) {
                    frame.classList.remove('dynamic-island');
                    frame.classList.add('notch');
                }
            }
        }

        function updateDevicePreview() {
            const size = document.getElementById('device-size').value;
            const frame = document.getElementById('phone-frame');
            
            if (size === 'desktop') {
                frame.classList.remove('mobile', 'dynamic-island', 'notch');
                frame.classList.add('desktop');
            } else {
                frame.classList.remove('desktop');
                frame.classList.add('mobile');
                // Re-apply detection logic for notch/island if switching back to mobile manually
                // For simplicity in manual switch, default to DI
                frame.classList.add('dynamic-island');
            }
        }

        // --- TITLE ANIMATION ---
        let isAnimating = false;

        function animateTitle() {
            if (isAnimating) return;
            isAnimating = true;

            const el = document.getElementById('animated-title');
            const ruler = document.getElementById('ruler');
            
            const seq = [
                { type: 'html', content: '<span class="dot white title-dot"></span>', time: 700 },
                { type: 'html', content: '<span class="dot orange title-dot"></span>', time: 700 },
                { type: 'html', content: '<span class="dot gray title-dot"></span>', time: 700 },
                { type: 'text', content: 'Grid.', time: 0 } 
            ];
            
            let i = 0;
            
            function step() {
                const item = seq[i];
                if (item.type === 'text') ruler.innerText = item.content;
                else ruler.innerHTML = item.content;
                
                const newWidth = ruler.offsetWidth;

                el.style.opacity = 0;
                
                setTimeout(() => {
                    el.style.width = newWidth + 'px';
                    
                    if (item.type === 'text') el.innerText = item.content;
                    else el.innerHTML = item.content;
                    
                    el.style.opacity = 1;
                    
                    i++;
                    if (i < seq.length) {
                        setTimeout(step, item.time);
                    } else {
                        isAnimating = false;
                    }
                    
                }, 200); 
            }
            step();
        }
        
        function replayAnimation() { animateTitle(); }

        window.onload = function() {
            // 1. Load Saved Data (skip device size to allow fresh detection)
            loadPreferences();
            
            // 2. Detect Current Device Type and override preview
            detectDeviceType();
            
            // 3. Init Title Width & Animation
            const el = document.getElementById('animated-title');
            const ruler = document.getElementById('ruler');
            ruler.innerText = "Grid.";
            el.style.width = ruler.offsetWidth + 'px';
            
            setTimeout(animateTitle, 2000);
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

        // --- LEGEND MODAL ---
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

        // --- RELEASE NOTES MODAL ---
        function openReleaseModal() { toggleReleaseModal(true); }
        function closeReleaseModal(e) { if(e.target === document.getElementById('releaseModalOverlay')) toggleReleaseModal(false); }
        function toggleReleaseModal(show) {
            const overlay = document.getElementById('releaseModalOverlay');
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

        function addDate(selM, selD, selE) {
            const container = document.getElementById('date-list');
            const div = document.createElement('div');
            div.className = 'date-row';
            div.innerHTML = `
                <div class="date-picker-group">
                    <select class="month-select">${getMonthOptionsHtml(selM)}</select>
                    <select class="day-select">${getDayOptionsHtml(selD)}</select>
                </div>
                <select class="emoji-select">${getEmojiOptionsHtml(selE)}</select>
                <button class="btn-icon btn-remove" onclick="removeDate(this)">×</button>
            `;
            container.appendChild(div);
        }

        function removeDate(btn) {
            const container = document.getElementById('date-list');
            if (container.children.length > 1) btn.parentElement.remove();
            else {
                const selects = btn.parentElement.querySelectorAll('select');
                selects.forEach(s => s.selectedIndex = 0);
            }
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
                
                // Show Mockup even for default
                document.getElementById('mockup-img').src = fullUrl;
                
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
            // 1. Save State
            savePreferences();

            const rows = document.querySelectorAll('.date-row');
            let dateEntries = [];
            
            rows.forEach(row => {
                const month = row.querySelector('.month-select').value;
                const day = row.querySelector('.day-select').value;
                const emoji = row.querySelector('.emoji-select').value;
                
                if (month && day) {
                    const mStr = month.toString().padStart(2, '0');
                    const dStr = day.toString().padStart(2, '0');
                    
                    let entry = `${mStr}-${dStr}`;
                    if (emoji) {
                        entry += `|${emoji}`;
                    }
                    dateEntries.push(entry);
                }
            });

            const sig = document.getElementById('signature').value.trim();
            const deviceSize = document.getElementById('device-size').value;
            const mode = document.getElementById('view-mode').value;
            const barStyle = document.getElementById('bar-style').value;
            const highlightWeekends = document.getElementById('weekend-toggle').checked;
            
            const val = dateEntries.join(',');
            
            const baseUrl = window.location.origin + "/api/image";
            const params = new URLSearchParams();
            
            if (val) params.append('dates', val);
            params.append('theme', selectedTheme);
            if (sig) params.append('signature', sig);
            if (mode !== 'year') params.append('mode', mode);
            if (barStyle !== 'segmented') params.append('bar_style', barStyle);
            if (highlightWeekends) params.append('highlight_weekends', 'true');
            if (deviceSize === 'desktop') params.append('size', 'desktop');
            
            const fullUrl = baseUrl + "?" + params.toString();
            const isDefault = dateEntries.length === 0 && selectedTheme === 'dark' && sig === '' && mode === 'year' && barStyle === 'segmented' && !highlightWeekends && deviceSize === 'mobile';

            // Set Mockup Image
            document.getElementById('mockup-img').src = fullUrl;

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

# --- NEW: SERVE FONTS TO FRONTEND ---
@app.route('/fonts/<path:filename>')
def serve_fonts(filename):
    return send_from_directory(FONT_DIR, filename)

@app.route('/api/image')
def generate_grid():
    # 1. Get Parameters
    dates_param = request.args.get('dates', '')
    theme_param = request.args.get('theme', 'dark')
    signature_param = request.args.get('signature', '')
    mode_param = request.args.get('mode', 'year')
    bar_style_param = request.args.get('bar_style', 'segmented')
    highlight_weekends_param = request.args.get('highlight_weekends', 'false') == 'true'

    # 2. Select Theme Colors
    palette = THEMES.get(theme_param, THEMES['dark'])
    
    # 3. Setup Time (IST)
    ist_offset = datetime.timedelta(hours=5, minutes=30)
    now = datetime.datetime.now(datetime.timezone.utc) + ist_offset
    current_year = now.year

    # 4. Parse Special Dates & Emojis early
    special_dates = {}
    if dates_param:
        items = dates_param.split(',')
        for item in items:
            if '|' in item:
                d_str, emoji = item.split('|', 1)
            else:
                d_str, emoji = item, None
            try:
                parts = d_str.strip().split('-')
                if len(parts) == 2:
                    m, d = int(parts[0]), int(parts[1])
                    try:
                        date_obj = datetime.date(current_year, m, d)
                        special_dates[date_obj] = emoji
                    except ValueError: pass
            except ValueError: pass

    # 5. Determine Grid Dimensions & Range (Shared)
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

    # Calculate global days left (common for all modes)
    start_date_global = datetime.date(current_year, 1, 1)
    end_date_global = datetime.date(current_year, 12, 31)
    total_days_global = (end_date_global - start_date_global).days + 1
    days_passed_global = (now.date() - start_date_global).days + 1
    if days_passed_global < 0: days_passed_global = 0
    if days_passed_global > total_days_global: days_passed_global = total_days_global
    days_left = total_days_global - days_passed_global

    # --- MODE SPECIFIC LOGIC ---
    if mode_param == 'segregated_months':
        # --- NEW YEAR CALENDAR MODE (12 Month Grid) ---
        
        # Grid Configuration for 12 months
        COLS = 3
        ROWS = 4
        
        # Visual config for mini-grids
        MONTH_DOT_RADIUS = 12
        MONTH_DOT_PADDING = 10
        MINI_GRID_COLS = 7 # 7 days wide
        
        # Calculate width of one month block
        # Width = (12*2 * 7) + (10 * 6) = 168 + 60 = 228 px
        BLOCK_WIDTH = (MONTH_DOT_RADIUS * 2 * MINI_GRID_COLS) + (MONTH_DOT_PADDING * (MINI_GRID_COLS - 1))
        
        # Calculate margins
        # Total content width = 3 * BLOCK_WIDTH + 2 * GAP
        BLOCK_GAP_X = 150
        TOTAL_CONTENT_WIDTH = (COLS * BLOCK_WIDTH) + ((COLS - 1) * BLOCK_GAP_X)
        START_X_GLOBAL = (IMAGE_WIDTH - TOTAL_CONTENT_WIDTH) // 2
        
        # Vertical Tuning (User Request)
        # Previous START_Y_GLOBAL was 350 (too high)
        START_Y_GLOBAL = 750 # Lowered to clear the clock area
        
        # Previous row step was 400 (too gapped)
        ROW_HEIGHT_STEP = 340 # Tightened vertical spacing
        
        month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        
        current_iter_date = datetime.date(current_year, 1, 1)
        
        for m in range(1, 13): # 1 to 12
            # Find grid position (0-2 col, 0-3 row)
            idx = m - 1
            row_idx = idx // COLS
            col_idx = idx % COLS
            
            month_start_x = START_X_GLOBAL + col_idx * (BLOCK_WIDTH + BLOCK_GAP_X)
            month_start_y = START_Y_GLOBAL + row_idx * (ROW_HEIGHT_STEP) 
            
            # Draw Month Name
            draw.text((month_start_x, month_start_y - 60), month_names[idx], font=font_small, fill=palette['INACTIVE'])
            
            # Draw Days for this month
            days_in_month = calendar.monthrange(current_year, m)[1]
            
            for d in range(1, days_in_month + 1):
                current_day_date = datetime.date(current_year, m, d)
                
                # Determine Color
                draw_color = palette['INACTIVE']
                if highlight_weekends_param and current_day_date.weekday() >= 5:
                    draw_color = palette['WEEKEND']
                
                draw_emoji_img = None
                
                if current_day_date in special_dates:
                    emoji_char = special_dates[current_day_date]
                    if emoji_char:
                        draw_emoji_img = get_emoji_image(emoji_char)
                        if not draw_emoji_img: draw_color = palette['SPECIAL']
                    else:
                        draw_color = palette['SPECIAL']
                elif current_day_date == now.date():
                    draw_color = palette['ACTIVE']
                elif current_day_date < now.date():
                    draw_color = palette['PASSED']

                # Calc dot position inside block (Row-major, 7 cols wide)
                d_idx = d - 1
                dot_row = d_idx // MINI_GRID_COLS
                dot_col = d_idx % MINI_GRID_COLS
                
                x = month_start_x + dot_col * (MONTH_DOT_RADIUS * 2 + MONTH_DOT_PADDING)
                y = month_start_y + dot_row * (MONTH_DOT_RADIUS * 2 + MONTH_DOT_PADDING)
                
                if draw_emoji_img:
                    target_size = (MONTH_DOT_RADIUS * 2, MONTH_DOT_RADIUS * 2)
                    emoji_resized = draw_emoji_img.resize(target_size, Image.Resampling.LANCZOS)
                    img.paste(emoji_resized, (int(x), int(y)), emoji_resized)
                else:
                    draw.ellipse((x, y, x + MONTH_DOT_RADIUS * 2, y + MONTH_DOT_RADIUS * 2), fill=draw_color)
        
        # Determine text Y for footer elements relative to the last row
        grid_bottom_y = START_Y_GLOBAL + (3 * ROW_HEIGHT_STEP) + 220

    else:
        # --- ORIGINAL MODES (Year, Quarter, Month, Fortnight) ---
        grid_cols = GRID_COLS
        grid_rows = GRID_ROWS
        dot_radius = DOT_RADIUS
        dot_spacing = DOT_PADDING
        
        if mode_param == 'month':
            start_date = datetime.date(current_year, now.month, 1)
            last_day = calendar.monthrange(current_year, now.month)[1]
            end_date = datetime.date(current_year, now.month, last_day)
            grid_cols, grid_rows = 7, 5
            dot_radius, dot_spacing = 35, 45
            days_left_mode = (end_date - now.date()).days
            if days_left_mode < 0: days_left_mode = 0
            range_text = now.strftime("%b")
            
        elif mode_param == 'quarter':
            q = (now.month - 1) // 3 + 1
            start_month = (q - 1) * 3 + 1
            end_month = start_month + 2
            start_date = datetime.date(current_year, start_month, 1)
            last_day_q = calendar.monthrange(current_year, end_month)[1]
            end_date = datetime.date(current_year, end_month, last_day_q)
            grid_cols, grid_rows = 10, 10
            dot_radius, dot_spacing = 25, 25
            days_left_mode = (end_date - now.date()).days
            if days_left_mode < 0: days_left_mode = 0
            range_text = f"Q{q}"

        elif mode_param == 'fortnight':
            start_date = now.date() - datetime.timedelta(days=now.weekday())
            end_date = start_date + datetime.timedelta(days=13)
            grid_cols, grid_rows = 7, 2
            dot_radius, dot_spacing = 45, 50
            days_left_mode = (end_date - now.date()).days
            if days_left_mode < 0: days_left_mode = 0
            range_text = "period"

        else: # Year (Default Single Grid)
            start_date = datetime.date(current_year, 1, 1)
            end_date = datetime.date(current_year, 12, 31)
            days_left_mode = days_left
            range_text = "year"
        
        # Common Draw Loop for these modes
        DOT_SPACING = dot_spacing
        total_grid_w = (grid_cols * (dot_radius * 2)) + ((grid_cols - 1) * DOT_SPACING)
        total_grid_h = (grid_rows * (dot_radius * 2)) + ((grid_rows - 1) * DOT_SPACING)
        
        start_x = (IMAGE_WIDTH - total_grid_w) // 2
        
        if mode_param == 'year':
            start_y = (IMAGE_HEIGHT // 2) - (total_grid_h // 2) + 150 
        else:
            start_y = (IMAGE_HEIGHT // 2) - (total_grid_h // 2)
        
        if start_y < 200: start_y = 200

        current_iter_date = start_date
        
        for row in range(grid_rows):
            for col in range(grid_cols):
                if current_iter_date > end_date: break
                
                # Color Logic
                draw_color = palette['INACTIVE']
                if highlight_weekends_param and current_iter_date.weekday() >= 5:
                    draw_color = palette['WEEKEND']
                
                draw_emoji_img = None
                if current_iter_date in special_dates:
                    emoji_char = special_dates[current_iter_date]
                    if emoji_char:
                        draw_emoji_img = get_emoji_image(emoji_char)
                        if not draw_emoji_img: draw_color = palette['SPECIAL']
                    else:
                        draw_color = palette['SPECIAL']
                elif current_iter_date == now.date():
                    draw_color = palette['ACTIVE']
                elif current_iter_date < now.date():
                    draw_color = palette['PASSED']

                x = int(start_x + col * (dot_radius * 2 + DOT_SPACING))
                y = int(start_y + row * (dot_radius * 2 + DOT_SPACING))

                if draw_emoji_img:
                    target_size = (dot_radius * 2, dot_radius * 2)
                    emoji_resized = draw_emoji_img.resize(target_size, Image.Resampling.LANCZOS)
                    img.paste(emoji_resized, (x, y), emoji_resized)
                else:
                    draw.ellipse((x, y, x + dot_radius * 2, y + dot_radius * 2), fill=draw_color)
                
                current_iter_date += datetime.timedelta(days=1)
        
        grid_bottom_y = start_y + total_grid_h

    # --- Draw Bottom Info (Common) ---
    # Recalculate range text for specific modes if needed, but 'year' is default fallback
    range_text_final = "year"
    if mode_param == 'month': range_text_final = now.strftime("%b")
    elif mode_param == 'quarter': range_text_final = f"Q{(now.month-1)//3 + 1}"
    elif mode_param == 'fortnight': range_text_final = "period"
    
    # Use global stats for Year modes
    if mode_param in ['year', 'segregated_months']:
        bottom_text = f"{days_left}d left in year"
        progress_ratio = days_passed_global / total_days_global if total_days_global > 0 else 0
    else:
        # Use local stats calculated in the else block above? 
        # Actually easier to re-calc local range here if needed or just use passed vars
        # For simplicity, let's just re-calc local days for progress bar
        if mode_param == 'month':
            s = datetime.date(current_year, now.month, 1)
            e = datetime.date(current_year, now.month, calendar.monthrange(current_year, now.month)[1])
        elif mode_param == 'quarter':
            q = (now.month - 1) // 3 + 1
            s = datetime.date(current_year, (q-1)*3+1, 1)
            e = datetime.date(current_year, (q-1)*3+3, calendar.monthrange(current_year, (q-1)*3+3)[1])
        elif mode_param == 'fortnight':
            s = now.date() - datetime.timedelta(days=now.weekday())
            e = s + datetime.timedelta(days=13)
        
        if mode_param not in ['year', 'segregated_months']:
            t = (e - s).days + 1
            p = (now.date() - s).days + 1
            if p < 0: p = 0
            if p > t: p = t
            bottom_text = f"{t-p}d left in {range_text_final}"
            progress_ratio = p / t if t > 0 else 0

    bbox_text = draw.textbbox((0, 0), bottom_text, font=font_small)
    text_width = bbox_text[2] - bbox_text[0]
    text_x = (IMAGE_WIDTH - text_width) / 2
    text_y = grid_bottom_y + 80
    draw.text((text_x, text_y), bottom_text, font=font_small, fill=palette['ACTIVE'])

    # --- Draw Progress Bar ---
    BAR_TOTAL_WIDTH = 600
    bar_start_x = (IMAGE_WIDTH - BAR_TOTAL_WIDTH) / 2
    bar_start_y = text_y + 60 

    if bar_style_param == 'solid':
        BAR_HEIGHT = 20
        draw.rounded_rectangle((bar_start_x, bar_start_y, bar_start_x + BAR_TOTAL_WIDTH, bar_start_y + BAR_HEIGHT), radius=10, fill=palette['INACTIVE'])
        fill_width = int(BAR_TOTAL_WIDTH * progress_ratio)
        if fill_width > 0:
            draw.rounded_rectangle((bar_start_x, bar_start_y, bar_start_x + fill_width, bar_start_y + BAR_HEIGHT), radius=10, fill=palette['ACTIVE'])
    elif bar_style_param == 'minimal':
        BAR_HEIGHT = 6
        draw.rounded_rectangle((bar_start_x, bar_start_y, bar_start_x + BAR_TOTAL_WIDTH, bar_start_y + BAR_HEIGHT), radius=3, fill=palette['INACTIVE'])
        fill_width = int(BAR_TOTAL_WIDTH * progress_ratio)
        if fill_width > 0:
            draw.rounded_rectangle((bar_start_x, bar_start_y, bar_start_x + fill_width, bar_start_y + BAR_HEIGHT), radius=3, fill=palette['ACTIVE'])
    else:
        BAR_HEIGHT = 20
        BAR_BLOCKS = 10
        BLOCK_GAP = 12
        single_block_width = (BAR_TOTAL_WIDTH - ((BAR_BLOCKS - 1) * BLOCK_GAP)) / BAR_BLOCKS
        filled_blocks = int(progress_ratio * BAR_BLOCKS)
        # Ensure at least one block is filled if any time passed
        if progress_ratio > 0 and filled_blocks == 0: filled_blocks = 1
        
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
        
        # Calculate specific signature gap
        sig_gap = 120
        if mode_param == 'segregated_months':
            sig_gap = 200 # Push it lower specifically for this mode
            
        sig_y = bar_start_y + BAR_HEIGHT + sig_gap
        draw.text((sig_x, sig_y), signature_param, font=font_signature, fill=palette['TEXT'])

    img_io = io.BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')