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

# --- Date Calculations (FIXED FOR IST) ---
# We force the script to look at Indian Standard Time (UTC + 5:30)
# This ensures that when GitHub runs at 18:30 UTC, the script calculates for 00:00 IST (Next Day)
ist_offset = datetime.timedelta(hours=5, minutes=30)
now = datetime.datetime.now(datetime.timezone.utc) + ist_offset

current_year = now.year
is_leap = calendar.isleap(current_year)
total_days_in_year = 366 if is_leap else 365
current_day_of_year = now.timetuple().tm_yday

days_left = total_days_in_year - current_day_of_year

# --- Special Dates Logic ---
env_dates = os.environ.get("SPECIAL_DATES", "")
special_days_indices = []

if env_dates:
    date_strings = env_dates.split(',')
    for d_str in date_strings:
        try:
            clean_str = d_str.strip()
            parts = clean_str.split('-')
            if len(parts) == 2:
                m, d = int(parts[0]), int(parts[1])
                try:
                    date_obj = datetime.date(current_year, m, d)
                    special_days_indices.append(date_obj.timetuple().tm_yday)
                except ValueError:
                    pass 
        except ValueError:
            pass

print(f"Generating image for Day {current_day_of_year} (IST).")

# --- Image Generation ---

img = Image.new('RGB', (IMAGE_WIDTH, IMAGE_HEIGHT), color=BG_COLOR)
draw = ImageDraw.Draw(img)

try:
    font_small = ImageFont.truetype(FONT_PATH, 40)
except IOError:
    print("ERROR: Font file not found. Please ensure fonts/Roboto-Regular.ttf exists.")
    exit(1)

# 1. Draw the Grid
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
        if dot_count in special_days_indices:
            color = DOT_COLOR_SPECIAL
        elif dot_count == current_day_of_year:
            color = DOT_COLOR_ACTIVE
        elif dot_count < current_day_of_year:
            color = DOT_COLOR_PASSED
        else:
            color = DOT_COLOR_INACTIVE

        x = start_x + col * (DOT_RADIUS * 2 + DOT_PADDING)
        y = start_y + row * (DOT_RADIUS * 2 + DOT_PADDING)

        draw.ellipse((x, y, x + DOT_RADIUS * 2, y + DOT_RADIUS * 2), fill=color)

# 2. Draw Bottom Text
bottom_text = f"{days_left}d left"
bbox_text = draw.textbbox((0, 0), bottom_text, font=font_small)
text_width = bbox_text[2] - bbox_text[0]
text_x = (IMAGE_WIDTH - text_width) / 2
text_y = IMAGE_HEIGHT - 220 # Moved up slightly to make room for bar

draw.text((text_x, text_y), bottom_text, font=font_small, fill=DOT_COLOR_ACTIVE)

# 3. Draw Progress Bar (Geometrically)
# We draw rounded rectangles manually. This is 100% reliable compared to fonts.

BAR_TOTAL_WIDTH = 600   # Total width of the progress bar in pixels
BAR_HEIGHT = 24         # Height of the blocks
BAR_BLOCKS = 10         # Number of blocks (10 blocks = 10% each)
BLOCK_GAP = 12          # Space between blocks

# Calculate the width of a single block
total_gap_width = (BAR_BLOCKS - 1) * BLOCK_GAP
single_block_width = (BAR_TOTAL_WIDTH - total_gap_width) / BAR_BLOCKS

# Logic for how many blocks to fill
progress_ratio = current_day_of_year / total_days_in_year
filled_blocks = int(progress_ratio * BAR_BLOCKS)

# The "Generous" Fix: If year has started, show at least 1 block
if current_day_of_year > 0 and filled_blocks == 0:
    filled_blocks = 1

# Center the bar horizontally
bar_start_x = (IMAGE_WIDTH - BAR_TOTAL_WIDTH) / 2
bar_start_y = text_y + 80 # 80 pixels below the text

for i in range(BAR_BLOCKS):
    # Calculate coordinates for this block
    b_x1 = bar_start_x + i * (single_block_width + BLOCK_GAP)
    b_y1 = bar_start_y
    b_x2 = b_x1 + single_block_width
    b_y2 = bar_start_y + BAR_HEIGHT
    
    # Determine color
    if i < filled_blocks:
        color = DOT_COLOR_ACTIVE     # Orange
    else:
        color = DOT_COLOR_INACTIVE   # Gray
        
    # Draw rounded rectangle
    draw.rounded_rectangle((b_x1, b_y1, b_x2, b_y2), radius=8, fill=color)

# Save
img.save("daily_status.png")
print("Successfully saved daily_status.png"
