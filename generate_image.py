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
# Using timezone-aware UTC to avoid warnings
now = datetime.datetime.now(datetime.timezone.utc)
current_year = now.year
is_leap = calendar.isleap(current_year)
total_days_in_year = 366 if is_leap else 365
current_day_of_year = now.timetuple().tm_yday

days_left = total_days_in_year - current_day_of_year

# --- Special Dates Logic (User Friendly) ---
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

print(f"Generating image for Day {current_day_of_year}.")
if special_days_indices:
    print(f"Special days loaded from settings: {special_days_indices}")

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

# --- Bottom Info ---

# 1. Text: "X days left"
bottom_text = f"{days_left}d left"
bbox_text = draw.textbbox((0, 0), bottom_text, font=font_small)
text_width = bbox_text[2] - bbox_text[0]
text_x = (IMAGE_WIDTH - text_width) / 2
text_y = IMAGE_HEIGHT - 200

draw.text((text_x, text_y), bottom_text, font=font_small, fill=DOT_COLOR_ACTIVE)

# 2. Progress Bar: "███░░░░░░░"
BAR_LENGTH = 10
progress_ratio = current_day_of_year / total_days_in_year
filled_blocks = int(progress_ratio * BAR_LENGTH)
empty_blocks = BAR_LENGTH - filled_blocks

# Construct the ASCII string
progress_bar_str = ("█" * filled_blocks) + ("░" * empty_blocks)

# Calculate position to center it below the text
bbox_bar = draw.textbbox((0, 0), progress_bar_str, font=font_small)
bar_width = bbox_bar[2] - bbox_bar[0]
bar_x = (IMAGE_WIDTH - bar_width) / 2
bar_y = text_y + 55  # 55 pixels below the text

draw.text((bar_x, bar_y), progress_bar_str, font=font_small, fill=DOT_COLOR_ACTIVE)

# Save
img.save("daily_status.png")
print("Successfully saved daily_status.png")