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
# Mobile Dimensions
MOBILE_WIDTH = 1170
MOBILE_HEIGHT = 2532

# Desktop Dimensions
DESKTOP_WIDTH = 1920
DESKTOP_HEIGHT = 1080

# Default Color Palettes
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
    if emoji_char in emoji_cache:
        return emoji_cache[emoji_char]
    
    try:
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
    <meta name="description" content="Visualize your year. Wallpaper generator for iOS, Mac & Windows.">

    <style>
        @font-face { font-family: 'SignatureFont'; src: url('/fonts/Buffalo.otf'); }

        body { 
            background: #1c1c1e; 
            color: white; 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; 
            display: flex; 
            flex-direction: column; 
            align-items: center; 
            min-height: 100dvh; 
            margin: 0; 
            padding: 5vh 20px 40px 20px; 
            box-sizing: border-box; 
            overflow-x: hidden; 
        }

        .header-section { margin-bottom: 30px; text-align: center; width: 100%; }
        h1 { font-weight: 900; letter-spacing: -1px; margin: 0 0 5px 0; font-size: 2.5rem; display: flex; align-items: center; justify-content: center; gap: 8px; }
        
        #animated-title {
            transition: width 0.4s cubic-bezier(0.25, 0.8, 0.25, 1), opacity 0.2s ease-in-out;
            opacity: 1; display: inline-flex; justify-content: center; align-items: center; 
            vertical-align: middle; overflow: hidden; white-space: nowrap; height: 40px; cursor: pointer;
        }
        
        #ruler { visibility: hidden; position: absolute; white-space: nowrap; font-weight: 900; font-size: 2.5rem; letter-spacing: -1px; pointer-events: none; }
        .title-dot { width: 28px; height: 28px; border-radius: 50%; display: inline-block; flex-shrink: 0; }
        .subtitle-container { display: flex; align-items: center; justify-content: center; gap: 8px; }
        p.subtitle { color: #888; text-align: center; line-height: 1.5; font-size: 0.95rem; margin: 0; }
        .info-btn { background: none; border: 1px solid #444; color: #888; border-radius: 50%; width: 20px; height: 20px; font-size: 12px; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.2s; font-family: serif; font-weight: bold; }
        .info-btn:hover { border-color: #ff693c; color: #ff693c; }

        .content-wrapper { flex-grow: 1; display: flex; flex-direction: column; align-items: center; width: 100%; max-width: 360px; margin-bottom: 40px; }

        button.generate-btn { background: #ff693c; color: white; border: none; padding: 15px 30px; border-radius: 12px; font-weight: bold; font-size: 16px; cursor: pointer; width: 100%; transition: all 0.3s; box-shadow: 0 4px 15px rgba(255, 105, 60, 0.3); }
        button.generate-btn:hover { opacity: 0.9; }
        button.generate-btn.success { background: #34c759 !important; box-shadow: 0 4px 15px rgba(52, 199, 89, 0.3); transform: scale(0.98); }

        .separator { display: flex; align-items: center; justify-content: center; width: 100%; margin: 25px 0; color: #555; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; }
        .separator::before, .separator::after { content: ""; flex: 1; border-bottom: 1px solid #333; margin: 0 10px; }

        .customise-trigger { color: #888; background: #252527; border: 1px solid #333; padding: 12px 20px; border-radius: 12px; font-size: 0.9rem; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 8px; transition: all 0.2s; font-weight: 500; width: 100%; box-sizing: border-box; }
        .customise-trigger:hover { background: #333; color: white; border-color: #555; }
        .arrow { font-size: 0.7rem; transition: transform 0.3s; }
        .customise-trigger.active .arrow { transform: rotate(180deg); }

        #custom-section { display: none; width: 100%; animation: slideDown 0.3s ease; border: 1px solid #333; border-radius: 12px; padding: 15px; margin-top: 10px; background: #232325; box-sizing: border-box; }
        h2 { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1px; color: #666; margin: 0 0 10px 0; }

        /* Form Elements */
        #date-list { display: flex; flex-direction: column; gap: 8px; margin-bottom: 15px; }
        .date-row { display: flex; gap: 8px; align-items: center; }
        .date-picker-group { display: flex; flex-grow: 1; gap: 5px; }
        select, input[type="text"] { background: #2c2c2e; border: 1px solid #444; padding: 10px; border-radius: 8px; color: white; font-family: inherit; font-size: 14px; outline: none; width: 100%; box-sizing: border-box; }
        .month-select { flex: 2; }
        .day-select { flex: 1; }
        .emoji-select { flex-grow: 0 !important; width: 60px !important; font-size: 18px !important; appearance: none; -webkit-appearance: none; text-align: center; text-align-last: center; }
        
        #signature { font-family: 'SignatureFont', cursive; font-size: 28px; letter-spacing: 1px; padding: 12px 10px; }
        #signature::placeholder { font-family: sans-serif; font-size: 14px; letter-spacing: normal; opacity: 0.5; }

        /* Toggles & Buttons */
        .toggle-container { display: flex; align-items: center; justify-content: space-between; background: #2c2c2e; padding: 12px; border-radius: 8px; border: 1px solid #444; margin-bottom: 20px; }
        .switch { position: relative; display: inline-block; width: 44px; height: 24px; }
        .switch input { opacity: 0; width: 0; height: 0; }
        .slider { position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: #444; transition: .4s; border-radius: 24px; }
        .slider:before { position: absolute; content: ""; height: 20px; width: 20px; left: 2px; bottom: 2px; background-color: white; transition: .4s; border-radius: 50%; }
        input:checked + .slider { background-color: #ff693c; }
        input:checked + .slider:before { transform: translateX(20px); }

        .btn-icon { background: #333; border: 1px solid #444; width: 38px; height: 38px; border-radius: 8px; display: flex; align-items: center; justify-content: center; cursor: pointer; color: #ff693c; font-size: 18px; flex-shrink: 0; }
        .btn-add { background: transparent; border: 1px dashed #444; color: #888; width: 100%; padding: 8px; border-radius: 8px; cursor: pointer; font-size: 13px; margin-bottom: 15px; }
        .btn-add:hover { border-color: #ff693c; color: #ff693c; }

        .theme-switch { display: flex; gap: 10px; background: #2c2c2e; padding: 4px; border-radius: 8px; width: 100%; box-sizing: border-box; margin-bottom: 15px; }
        .theme-option { flex: 1; text-align: center; padding: 8px; border-radius: 6px; cursor: pointer; font-weight: 600; font-size: 13px; color: #888; transition: all 0.2s; }
        .theme-option.active { background: #444; color: white; }

        button.generate-custom-btn { background: #333; color: white; border: 1px solid #555; padding: 12px; border-radius: 8px; font-weight: bold; font-size: 14px; cursor: pointer; width: 100%; }
        button.generate-custom-btn:hover { background: #ff693c; border-color: #ff693c; }

        /* Results Area */
        .result { margin-top: 20px; display: none; text-align: center; animation: slideUp 0.5s ease; width: 100%; border-top: 1px solid #333; padding-top: 20px; }
        .url-container { display: flex; gap: 10px; margin: 10px 0; }
        .url-box { background: #000; padding: 12px; border-radius: 8px; font-family: monospace; font-size: 13px; color: #ff693c; border: 1px solid #333; flex-grow: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .copy-btn { background: #333; border: 1px solid #444; border-radius: 8px; cursor: pointer; color: white; padding: 0 15px; font-weight: bold; }

        /* MOCKUPS */
        .iphone-mockup { width: 280px; aspect-ratio: 9 / 19.5; background: #000; border-radius: 40px; border: 8px solid #2b2b2b; position: relative; margin: 20px auto; overflow: hidden; box-shadow: 0 20px 40px rgba(0,0,0,0.6); }
        .iphone-mockup.dynamic-island .dynamic-island { width: 80px; height: 24px; background: #000; position: absolute; top: 12px; left: 50%; transform: translateX(-50%); border-radius: 20px; z-index: 10; }
        
        .monitor-mockup { width: 320px; aspect-ratio: 16 / 9; background: #000; border: 10px solid #2b2b2b; border-bottom-width: 15px; position: relative; margin: 20px auto; overflow: hidden; box-shadow: 0 20px 40px rgba(0,0,0,0.6); border-radius: 8px; display: none;}
        .monitor-stand { width: 80px; height: 30px; background: #222; margin: -20px auto 20px auto; border-radius: 0 0 10px 10px; }
        
        .mockup-img { width: 100%; height: 100%; object-fit: cover; display: block; }

        .shortcut-section { margin-top: 20px; background: #2c2c2e; padding: 15px; border-radius: 12px; border: 1px solid #444; }
        .shortcut-btn { background: white; color: black; display: block; width: 100%; padding: 12px; border-radius: 8px; font-weight: bold; text-decoration: none; margin-top: 10px; box-sizing: border-box; cursor: pointer; }

        footer { margin-top: auto; color: #555; font-family: 'Courier New', monospace; font-size: 13px; opacity: 0.8; padding-bottom: 10px; width: 100%; text-align: center; }
        .footer-link { color: #555; text-decoration: none; border-bottom: 1px dotted #555; cursor: pointer; }

        /* MODALS */
        .modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0, 0, 0, 0.7); backdrop-filter: blur(5px); z-index: 1000; display: none; align-items: center; justify-content: center; opacity: 0; transition: opacity 0.3s; }
        .modal { background: #1c1c1e; border: 1px solid #333; padding: 25px; border-radius: 16px; width: 90%; max-width: 320px; transform: scale(0.9); transition: transform 0.3s; max-height: 80vh; overflow-y: auto; }
        
        .color-legend { display: flex; flex-direction: column; gap: 15px; margin-top: 20px; }
        .legend-item { display: flex; align-items: center; gap: 15px; font-size: 0.95rem; color: #ccc; }
        .dot { width: 16px; height: 16px; border-radius: 50%; display: inline-block; flex-shrink: 0; }
        .dot.white { background: #fff; border: 1px solid #444; }
        .dot.orange { background: #ff693c; }
        .dot.gray { background: #444446; }
        .close-modal { background: #333; border: none; color: white; width: 100%; padding: 12px; border-radius: 10px; margin-top: 25px; cursor: pointer; font-weight: 600; }
        
        .code-block { background: #000; padding: 10px; border-radius: 6px; font-family: monospace; font-size: 11px; color: #34c759; overflow-x: auto; white-space: pre; border: 1px solid #333; margin: 10px 0; }
        .platform-tabs { display: flex; gap: 5px; margin-bottom: 15px; }
        .tab { flex: 1; background: #333; padding: 8px; font-size: 12px; text-align: center; cursor: pointer; border-radius: 6px; color: #888; }
        .tab.active { background: #ff693c; color: white; }

        @keyframes slideDown { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes slideUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
    </style>
</head>
<body>
    <div class="header-section">
        <span id="ruler"></span>
        <h1>The <span id="animated-title" onclick="replayAnimation()">Grid.</span></h1>
        <div class="subtitle-container">
            <p class="subtitle" id="device-subtitle">Visualize your year.</p>
            <button class="info-btn" onclick="openModal()" title="Legend">i</button>
        </div>
    </div>
    
    <div class="content-wrapper">
        <button class="generate-btn" id="default-btn" onclick="generateDefault()">Get The Grid</button>
        <div class="separator">OR</div>
        <div class="customise-trigger" onclick="toggleCustomise(this)">
            <span>Customise</span><span class="arrow">▼</span>
        </div>

        <div id="custom-section">
            <h2>View Mode</h2>
            <div style="margin-bottom: 20px;">
                <select id="view-mode" style="width: 100%">
                    <option value="year">Full Year (Default)</option>
                    <option value="segregated_months">Segregated Months</option>
                    <option value="quarter">Current Quarter</option>
                    <option value="month">Current Month</option>
                </select>
            </div>
            <h2>Visuals</h2>
            <div class="toggle-container">
                <span class="toggle-label">Highlight Weekends</span>
                <label class="switch"><input type="checkbox" id="weekend-toggle"><span class="slider"></span></label>
            </div>
            <h2>Progress Bar</h2>
            <div style="margin-bottom: 20px;">
                <select id="bar-style" style="width: 100%">
                    <option value="segmented">Segmented</option>
                    <option value="solid">Solid</option>
                    <option value="minimal">Minimal</option>
                </select>
            </div>
            <h2>Important Dates</h2>
            <div id="date-list"></div>
            <button class="btn-add" onclick="addDate()">+ Add another date</button>
            <h2>Theme</h2>
            <div class="theme-switch">
                <label class="theme-option active" id="lbl-dark" onclick="setTheme('dark')">Dark<input type="radio" name="theme" value="dark" checked></label>
                <label class="theme-option" id="lbl-light" onclick="setTheme('light')">Light<input type="radio" name="theme" value="light"></label>
            </div>
            <h2>Signature</h2>
            <div style="margin-bottom: 20px;"><input type="text" id="signature" placeholder="Add your signature..." maxlength="20"></div>
            <button class="generate-custom-btn" onclick="generateCustom()">Generate Custom Link</button>
        </div>

        <div class="result" id="result">
            <div id="custom-url-display">
                <p style="margin-bottom: 5px; font-size: 0.9rem; color: #888;">Step 1: Copy this URL.</p>
                <div class="url-container">
                    <div class="url-box" id="urlBox"></div>
                    <button class="copy-btn" onclick="copyToClipboard()">Copy</button>
                </div>
            </div>

            <div id="phone-frame" class="iphone-mockup dynamic-island">
                <div class="dynamic-island"></div>
                <img id="mockup-img" class="mockup-img" src="" alt="Preview">
            </div>

            <div id="monitor-frame" class="monitor-mockup">
                <img id="monitor-img" class="mockup-img" src="" alt="Preview">
            </div>
            <div id="monitor-stand" class="monitor-stand" style="display:none"></div>

            <div class="shortcut-section">
                <p style="margin: 0 0 10px 0; font-size: 0.9rem; color: #ccc;">Step 2: Automate it.</p>
                <button onclick="openAutomationModal()" class="shortcut-btn">View Setup Instructions</button>
            </div>
        </div>
    </div>

    <footer>
        &lt;/&gt; with ❤️ by Spandan.<br>
        <span onclick="openReleaseModal()" class="footer-link">Version 4.0 Multi-Platform</span>
    </footer>

    <div class="modal-overlay" id="modalOverlay" onclick="closeModal(event)">
        <div class="modal">
            <h3>The Legend</h3>
            <div class="color-legend">
                <div class="legend-item"><span class="dot white"></span><span><strong>The Past:</strong> Gone.</span></div>
                <div class="legend-item"><span class="dot orange"></span><span><strong>The Present:</strong> Today.</span></div>
                <div class="legend-item"><span class="dot gray"></span><span><strong>The Future:</strong> The void.</span></div>
            </div>
            <button class="close-modal" onclick="toggleModal(false)">Close</button>
        </div>
    </div>

    <div class="modal-overlay" id="autoModalOverlay" onclick="closeAutoModal(event)">
        <div class="modal" style="max-width: 500px;">
            <h3>Automate Wallpaper</h3>
            <div class="platform-tabs">
                <div class="tab active" onclick="showTab('ios')" id="tab-ios">iOS</div>
                <div class="tab" onclick="showTab('win')" id="tab-win">Windows</div>
                <div class="tab" onclick="showTab('mac')" id="tab-mac">Mac</div>
            </div>

            <div id="content-ios">
                <p style="font-size:0.9rem; color:#ccc;">Use the Shortcuts app.</p>
                <a href="https://www.icloud.com/shortcuts/99a190f4001844f9ade585fc8eafd47e" class="shortcut-btn" target="_blank" style="text-align:center; border:1px solid #ccc;">Install iOS Shortcut</a>
            </div>

            <div id="content-win" style="display:none">
                <p style="font-size:0.9rem; color:#ccc;">1. Open <strong>Task Scheduler</strong>.<br>2. Create Basic Task (Daily).<br>3. Action: "Start a Program".<br>4. Program: <code>powershell.exe</code><br>5. Arguments (Paste this):</p>
                <div class="code-block" id="win-code"></div>
                <p style="font-size:0.8rem; color:#666;">Note: Replaces 'C:\wallpaper.png'</p>
            </div>

            <div id="content-mac" style="display:none">
                <p style="font-size:0.9rem; color:#ccc;">1. Open <strong>Automator</strong> -> Application.<br>2. Add action: <strong>"Get Specified URLs"</strong> (Paste your link).<br>3. Add action: <strong>"Download URLs"</strong>.<br>4. Add action: <strong>"Set Desktop Picture"</strong>.<br>5. Save as App & Add to Login Items.</p>
            </div>
            
            <button class="close-modal" onclick="toggleAutoModal(false)">Close</button>
        </div>
    </div>

    <script>
        // --- LOGIC ---
        let currentPlatform = 'mobile'; // 'mobile' | 'desktop'
        const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

        function detectPlatform() {
            const userAgent = navigator.userAgent.toLowerCase();
            const isMobile = /iphone|ipad|ipod|android/i.test(userAgent);
            
            if (!isMobile) {
                currentPlatform = 'desktop';
                document.getElementById('device-subtitle').innerText = "Visualize your year (Desktop Mode).";
                // Swap Mockups
                document.getElementById('phone-frame').style.display = 'none';
                document.getElementById('monitor-frame').style.display = 'block';
                document.getElementById('monitor-stand').style.display = 'block';
                // Default Tab
                showTab(userAgent.includes('mac') ? 'mac' : 'win');
            } else {
                document.getElementById('device-subtitle').innerText = "Visualize your year (Mobile Mode).";
            }
        }

        function getLink(customDates, theme, sig, mode, bar, weekends) {
            const baseUrl = window.location.origin + "/api/image";
            const params = new URLSearchParams();
            if(customDates) params.append('dates', customDates);
            params.append('theme', theme);
            if(sig) params.append('signature', sig);
            params.append('mode', mode);
            params.append('bar_style', bar);
            if(weekends) params.append('highlight_weekends', 'true');
            params.append('platform', currentPlatform);
            return baseUrl + "?" + params.toString();
        }

        function generateDefault() {
            const link = getLink('', 'dark', '', 'year', 'segmented', false);
            handleResult(link);
        }

        function generateCustom() {
            // Collect Dates
            const rows = document.querySelectorAll('.date-row');
            let dateEntries = [];
            rows.forEach(row => {
                const m = row.querySelector('.month-select').value;
                const d = row.querySelector('.day-select').value;
                const e = row.querySelector('.emoji-select').value;
                if (m && d) {
                    let entry = `${m.padStart(2,'0')}-${d.padStart(2,'0')}`;
                    if (e) entry += `|${e}`;
                    dateEntries.push(entry);
                }
            });
            const theme = document.querySelector('input[name="theme"]:checked').value;
            const sig = document.getElementById('signature').value;
            const mode = document.getElementById('view-mode').value;
            const bar = document.getElementById('bar-style').value;
            const weekends = document.getElementById('weekend-toggle').checked;

            const link = getLink(dateEntries.join(','), theme, sig, mode, bar, weekends);
            handleResult(link);
        }

        function handleResult(url) {
            document.getElementById('urlBox').innerText = url;
            document.getElementById('result').style.display = "block";
            
            if(currentPlatform === 'desktop') {
                document.getElementById('monitor-img').src = url;
                // Generate Powershell Snippet
                const psCode = `Invoke-WebRequest -Uri "${url}" -OutFile "C:\\wallpaper.png"\nSet-ItemProperty -Path "HKCU:\\Control Panel\\Desktop" -Name Wallpaper -Value "C:\\wallpaper.png"\nRUNDLL32.EXE user32.dll,UpdatePerUserSystemParameters`;
                document.getElementById('win-code').innerText = psCode;
            } else {
                document.getElementById('mockup-img').src = url;
            }
            document.getElementById('result').scrollIntoView({ behavior: 'smooth' });
        }

        // --- Helper Functions ---
        function copyToClipboard() {
            navigator.clipboard.writeText(document.getElementById('urlBox').innerText);
            alert("Copied!");
        }

        // --- Init ---
        window.onload = function() {
            detectPlatform();
            addDate(); // Add one empty date row
            animateTitle();
        };

        // --- Animation ---
        function animateTitle() {
            const el = document.getElementById('animated-title');
            const ruler = document.getElementById('ruler');
            ruler.innerText = "Grid.";
            el.style.width = ruler.offsetWidth + 'px';
        }
        function replayAnimation() { animateTitle(); }

        // --- Modals ---
        function openModal() { document.getElementById('modalOverlay').style.display = 'flex'; setTimeout(()=>document.getElementById('modalOverlay').style.opacity=1,10); }
        function closeModal(e) { if(e.target.id === 'modalOverlay') toggleModal(false); }
        function toggleModal(s) { document.getElementById('modalOverlay').style.opacity=s?1:0; setTimeout(()=>document.getElementById('modalOverlay').style.display=s?'flex':'none',300); }
        
        function openAutomationModal() { document.getElementById('autoModalOverlay').style.display = 'flex'; setTimeout(()=>document.getElementById('autoModalOverlay').style.opacity=1,10); }
        function closeAutoModal(e) { if(e.target.id === 'autoModalOverlay') toggleAutoModal(false); }
        function toggleAutoModal(s) { document.getElementById('autoModalOverlay').style.opacity=s?1:0; setTimeout(()=>document.getElementById('autoModalOverlay').style.display=s?'flex':'none',300); }

        function showTab(t) {
            ['ios','win','mac'].forEach(x => {
                document.getElementById(`content-${x}`).style.display = x===t ? 'block' : 'none';
                document.getElementById(`tab-${x}`).className = x===t ? 'tab active' : 'tab';
            });
        }

        // --- Date Picker Logic ---
        function getMonthOptionsHtml() { return `<option value="" disabled selected>M</option>` + MONTHS.map((m,i)=>`<option value="${i+1}">${m}</option>`).join(''); }
        function getDayOptionsHtml() { return `<option value="" disabled selected>D</option>` + Array.from({length:31},(_,i)=>`<option value="${i+1}">${i+1}</option>`).join(''); }
        function getEmojiOptionsHtml() { return ["🟡", "🍰", "❤️", "🚀", "💰"].map(e => `<option value="${e=='🟡'?'':e}">${e}</option>`).join(''); }

        function addDate() {
            const div = document.createElement('div'); div.className = 'date-row';
            div.innerHTML = `<div class="date-picker-group"><select class="month-select">${getMonthOptionsHtml()}</select><select class="day-select">${getDayOptionsHtml()}</select></div><select class="emoji-select">${getEmojiOptionsHtml()}</select><button class="btn-icon" onclick="this.parentElement.remove()">×</button>`;
            document.getElementById('date-list').appendChild(div);
        }
        
        function toggleCustomise(t) { 
            const s = document.getElementById('custom-section'); 
            const isHidden = s.style.display !== 'block';
            s.style.display = isHidden ? 'block' : 'none';
            if(isHidden) t.classList.add('active'); else t.classList.remove('active');
        }
        function setTheme(t) {
            document.getElementById('lbl-dark').className = t==='dark'?'theme-option active':'theme-option';
            document.getElementById('lbl-light').className = t==='light'?'theme-option active':'theme-option';
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return HTML_DASHBOARD

@app.route('/fonts/<path:filename>')
def serve_fonts(filename):
    return send_from_directory(FONT_DIR, filename)

@app.route('/api/image')
def generate_grid():
    # 1. Parameters
    dates_param = request.args.get('dates', '')
    theme_param = request.args.get('theme', 'dark')
    signature_param = request.args.get('signature', '')
    mode_param = request.args.get('mode', 'year')
    bar_style_param = request.args.get('bar_style', 'segmented')
    highlight_weekends = request.args.get('highlight_weekends', 'false') == 'true'
    platform_param = request.args.get('platform', 'mobile')

    # 2. Config based on Platform
    is_desktop = platform_param == 'desktop'
    IMG_W = DESKTOP_WIDTH if is_desktop else MOBILE_WIDTH
    IMG_H = DESKTOP_HEIGHT if is_desktop else MOBILE_HEIGHT
    
    palette = THEMES.get(theme_param, THEMES['dark'])
    ist_offset = datetime.timedelta(hours=5, minutes=30)
    now = datetime.datetime.now(datetime.timezone.utc) + ist_offset
    current_year = now.year

    # 3. Parse Dates
    special_dates = {}
    if dates_param:
        for item in dates_param.split(','):
            if '|' in item: d_str, emoji = item.split('|', 1)
            else: d_str, emoji = item, None
            try:
                m, d = map(int, d_str.strip().split('-'))
                special_dates[datetime.date(current_year, m, d)] = emoji
            except: pass

    # 4. Canvas
    img = Image.new('RGB', (IMG_W, IMG_H), color=palette['BG'])
    draw = ImageDraw.Draw(img)
    try: font_small = ImageFont.truetype(FONT_PATH, 40)
    except: font_small = ImageFont.load_default()
    try: font_sig = ImageFont.truetype(FONT_SIGNATURE_PATH, 55)
    except: font_sig = font_small

    # 5. Drawing Logic
    start_date_global = datetime.date(current_year, 1, 1)
    end_date_global = datetime.date(current_year, 12, 31)
    total_days_global = (end_date_global - start_date_global).days + 1
    days_passed = (now.date() - start_date_global).days + 1
    days_passed = max(0, min(days_passed, total_days_global))
    days_left = total_days_global - days_passed

    # --- Mode: Segregated Months ---
    if mode_param == 'segregated_months':
        # Layout Config
        if is_desktop:
            COLS, ROWS = 6, 2
            START_Y = 250
            GAP_X = 100
        else:
            COLS, ROWS = 3, 4
            START_Y = 750
            GAP_X = 150
            
        MINI_GRID_COLS = 7
        DOT_R = 12
        DOT_P = 10
        
        BLOCK_W = (DOT_R * 2 * MINI_GRID_COLS) + (DOT_P * (MINI_GRID_COLS - 1))
        CONTENT_W = (COLS * BLOCK_W) + ((COLS - 1) * GAP_X)
        START_X = (IMG_W - CONTENT_W) // 2
        ROW_H = 340 if not is_desktop else 320

        month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

        for m in range(1, 13):
            idx = m - 1
            r_idx = idx // COLS
            c_idx = idx % COLS
            
            m_x = START_X + c_idx * (BLOCK_W + GAP_X)
            m_y = START_Y + r_idx * ROW_H

            draw.text((m_x, m_y - 40), month_names[idx], font=font_small, fill=palette['INACTIVE'])
            
            days_in_m = calendar.monthrange(current_year, m)[1]
            for d in range(1, days_in_m + 1):
                curr_date = datetime.date(current_year, m, d)
                col = palette['INACTIVE']
                
                # Weekend Highlight
                if highlight_weekends and curr_date.weekday() >= 5: col = palette['WEEKEND']
                
                emoji_img = None
                if curr_date in special_dates:
                    if special_dates[curr_date]: emoji_img = get_emoji_image(special_dates[curr_date])
                    if not emoji_img: col = palette['SPECIAL']
                elif curr_date == now.date(): col = palette['ACTIVE']
                elif curr_date < now.date(): col = palette['PASSED']

                dot_idx = d - 1
                dot_r = dot_idx // MINI_GRID_COLS
                dot_c = dot_idx % MINI_GRID_COLS
                
                x = m_x + dot_c * (DOT_R*2 + DOT_P)
                y = m_y + dot_r * (DOT_R*2 + DOT_P)

                if emoji_img:
                    e_rz = emoji_img.resize((DOT_R*2, DOT_R*2), Image.Resampling.LANCZOS)
                    img.paste(e_rz, (int(x), int(y)), e_rz)
                else:
                    draw.ellipse((x, y, x + DOT_R*2, y + DOT_R*2), fill=col)
        
        grid_bottom_y = START_Y + (ROWS * ROW_H) + (50 if is_desktop else 220)

    else:
        # --- Mode: Year/Quarter/Month (Single Grid) ---
        if mode_param == 'month':
             # Logic same for both, centering handles it
             s_d = datetime.date(current_year, now.month, 1)
             e_d = datetime.date(current_year, now.month, calendar.monthrange(current_year, now.month)[1])
             g_c, g_r = 7, 5
             d_r, d_p = 35, 45
             txt = now.strftime("%b")
        elif mode_param == 'quarter':
            q = (now.month - 1) // 3 + 1
            s_d = datetime.date(current_year, (q-1)*3+1, 1)
            last = calendar.monthrange(current_year, (q-1)*3+3)[1]
            e_d = datetime.date(current_year, (q-1)*3+3, last)
            g_c, g_r = 10, 10
            d_r, d_p = 25, 25
            txt = f"Q{q}"
        else: 
            # YEAR MODE
            s_d = start_date_global
            e_d = end_date_global
            txt = "year"
            if is_desktop:
                # Desktop Year Grid (Wider)
                g_c, g_r = 32, 12
                d_r, d_p = 15, 15 
            else:
                # Mobile Year Grid (Taller)
                g_c, g_r = 15, 25
                d_r, d_p = 18, 15

        # Draw Grid
        grid_w = (g_c * d_r*2) + ((g_c-1)*d_p)
        grid_h = (g_r * d_r*2) + ((g_r-1)*d_p)
        start_x = (IMG_W - grid_w) // 2
        
        if is_desktop:
            start_y = (IMG_H - grid_h) // 2 - 50 # Slightly higher on desktop
        else:
            start_y = (IMG_H - grid_h) // 2 + 100

        curr = s_d
        for r in range(g_r):
            for c in range(g_c):
                if curr > e_d: break
                
                col = palette['INACTIVE']
                if highlight_weekends and curr.weekday() >= 5: col = palette['WEEKEND']
                
                emo = None
                if curr in special_dates:
                    if special_dates[curr]: emo = get_emoji_image(special_dates[curr])
                    if not emo: col = palette['SPECIAL']
                elif curr == now.date(): col = palette['ACTIVE']
                elif curr < now.date(): col = palette['PASSED']
                
                x = int(start_x + c*(d_r*2 + d_p))
                y = int(start_y + r*(d_r*2 + d_p))
                
                if emo:
                    rz = emo.resize((d_r*2, d_r*2), Image.Resampling.LANCZOS)
                    img.paste(rz, (x,y), rz)
                else:
                    draw.ellipse((x,y,x+d_r*2,y+d_r*2), fill=col)
                curr += datetime.timedelta(days=1)
        
        grid_bottom_y = start_y + grid_h

    # --- Footer Info ---
    # Progress Bar Text
    if mode_param == 'year' or mode_param == 'segregated_months':
        btm_txt = f"{days_left}d left in year"
        ratio = days_passed / total_days_global
    else:
        # Simplified calc for other modes
        t_d = (e_d - s_d).days + 1
        p_d = max(0, min((now.date() - s_d).days + 1, t_d))
        btm_txt = f"{t_d - p_d}d left in {txt}"
        ratio = p_d / t_d

    bbox = draw.textbbox((0,0), btm_txt, font=font_small)
    tx_w = bbox[2]-bbox[0]
    tx_x = (IMG_W - tx_w)/2
    tx_y = grid_bottom_y + (60 if is_desktop else 80)
    
    draw.text((tx_x, tx_y), btm_txt, font=font_small, fill=palette['ACTIVE'])

    # Bar
    BAR_W = 800 if is_desktop else 600
    b_x = (IMG_W - BAR_W)/2
    b_y = tx_y + 60
    BAR_H = 20
    
    # Simple Bar Logic (Segments hard to scale dynamically, using solid/minimal logic)
    if bar_style_param == 'minimal':
        draw.rounded_rectangle((b_x, b_y, b_x+BAR_W, b_y+6), radius=3, fill=palette['INACTIVE'])
        if ratio > 0: draw.rounded_rectangle((b_x, b_y, b_x+(BAR_W*ratio), b_y+6), radius=3, fill=palette['ACTIVE'])
    elif bar_style_param == 'solid':
        draw.rounded_rectangle((b_x, b_y, b_x+BAR_W, b_y+20), radius=10, fill=palette['INACTIVE'])
        if ratio > 0: draw.rounded_rectangle((b_x, b_y, b_x+(BAR_W*ratio), b_y+20), radius=10, fill=palette['ACTIVE'])
    else: # Segmented
         BLOCKS = 20 if is_desktop else 10
         GAP = 10
         s_w = (BAR_W - (BLOCKS-1)*GAP)/BLOCKS
         filled = int(ratio * BLOCKS)
         if ratio > 0 and filled == 0: filled = 1
         for i in range(BLOCKS):
             bx1 = b_x + i*(s_w+GAP)
             c = palette['ACTIVE'] if i < filled else palette['INACTIVE']
             draw.rounded_rectangle((bx1, b_y, bx1+s_w, b_y+20), radius=8, fill=c)

    # Signature
    if signature_param:
        sb = draw.textbbox((0,0), signature_param, font=font_sig)
        sw = sb[2]-sb[0]
        sx = (IMG_W - sw)/2
        sy = b_y + 40 + (50 if is_desktop else 100)
        draw.text((sx, sy), signature_param, font=font_sig, fill=palette['TEXT'])

    out = io.BytesIO()
    img.save(out, 'PNG')
    out.seek(0)
    return send_file(out, mimetype='image/png')

if __name__ == '__main__':
    app.run(debug=True)