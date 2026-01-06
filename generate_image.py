import datetime
import calendar
from PIL import Image, ImageDraw, ImageFont
import os

# --- Configuration ---
IMAGE_WIDTH = 1170
IMAGE_HEIGHT = 2532
BG_COLOR = (28, 28, 30)

# Color definitions
DOT_COLOR_ACTIVE = (255, 105, 60)   # Orange (Today)
DOT_COLOR_PASSED = (255, 255, 255)  # White (Passed days)
DOT_COLOR_INACTIVE = (68, 68, 70)   # Dim gray (Future days)
DOT_COLOR_SPECIAL = (255, 215, 0)   # Gold/Yellow (Special dates)
TEXT_COLOR = (255, 255, 255)

FONT_PATH = "fonts/Roboto-Regular.ttf"

# Grid configuration
GRID_COLS = 15
GRID_ROWS = 25
DOT_RADIUS = 18
DOT_PADDING = 22

# --- Date Calculations ---
now = datetime.datetime.now(datetime.timezone.utc)
current_year = now.year
is_leap = calendar.isleap(current_year)
total_days_in_year = 366 if is_leap else 365
current_day_of_year = now.timetuple().tm_yday

days_left = total_days_in_year - current_day_of_year

# --- Special Dates Logic (User Friendly) ---
# We check for a GitHub Repository Variable named "SPECIAL_DATES"
# Format expected: "03-02, 04-29, 12-10" (MM-DD)
env_dates = os.environ.get("SPECIAL_DATES", "")

special_days_indices = []

if env_dates:
    # Split the string by commas
    date_strings = env_dates.split(',')
    
    for d_str in date_strings:
        try:
            # Clean up whitespace and split by hyphen
            clean_str = d_str.strip()
            parts = clean_str.split('-')
            
            if len(parts) == 2:
                m, d = int(parts[0]), int(parts[1])
                # Convert date to Day of Year (1-366)
                try:
                    date_obj = datetime.date(current_year, m, d)
                    special_days_indices.append(date_obj.timetuple().tm_yday)
                except ValueError:
                    pass # Ignore invalid dates (e.g. Feb 30)
        except ValueError:
            pass

print(f"Generating image for Day {current_day_of_year}.")
if special_days_indices:
    print(f"Special days loaded from settings: {special_days_indices}")
else:
    print("No special dates found in settings (Environment Variable 'SPECIAL_DATES' is empty).")

# --- Image Generation ---

img = Image.new('RGB', (IMAGE_WIDTH, IMAGE_HEIGHT), color=BG_COLOR)
draw = ImageDraw.Draw(img)

try:
    font_small = ImageFont.truetype(FONT_PATH, 40)
except IOError:
    print("ERROR: Font file not found. Please ensure fonts/Roboto-Regular.ttf exists.")
    exit(1)

# Draw the Grid
total_grid_width = (GRID_COLS * (DOT_RADIUS * 2)) + ((GRID_COLS - 1) * DOT_PADDING)
total_grid_height = (GRID_ROWS * (DOT_RADIUS * 2)) + ((GRID_ROWS - 1) * DOT_PADDING)

start_x = (IMAGE_WIDTH - total_grid_width) // 2
start_y = (IMAGE_HEIGHT - total_grid_height) // 2 + 100

dot_count = 0
for row in range(GRID_ROWS):
    for col in range(GRID_COLS):
        dot_count += 1
        
        if dot_count > total_days_in_year:
            break

        # --- Color Logic ---
        
        # 1. Check for Special Dates (Yellow)
        if dot_count in special_days_indices:
            color = DOT_COLOR_SPECIAL
            
        # 2. Check for Today (Orange)
        elif dot_count == current_day_of_year:
            color = DOT_COLOR_ACTIVE
            
        # 3. Check for Past (White)
        elif dot_count < current_day_of_year:
            color = DOT_COLOR_PASSED
            
        # 4. Future (Gray)
        else:
            color = DOT_COLOR_INACTIVE

        # Position
        x = start_x + col * (DOT_RADIUS * 2 + DOT_PADDING)
        y = start_y + row * (DOT_RADIUS * 2 + DOT_PADDING)

        draw.ellipse((x, y, x + DOT_RADIUS * 2, y + DOT_RADIUS * 2), fill=color)

# Draw Bottom Text
bottom_text = f"{days_left}d left"
bbox_small = draw.textbbox((0, 0), bottom_text, font=font_small)
small_text_width = bbox_small[2] - bbox_small[0]
draw.text(((IMAGE_WIDTH - small_text_width) / 2, IMAGE_HEIGHT - 200), bottom_text, font=font_small, fill=DOT_COLOR_ACTIVE)

# Save
img.save("daily_status.png")
print("Successfully saved daily_status.png")