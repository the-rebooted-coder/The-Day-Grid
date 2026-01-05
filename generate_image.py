import datetime
import calendar
from PIL import Image, ImageDraw, ImageFont
import os

# --- Configuration ---
IMAGE_WIDTH = 1170  # roughly iPhone resolution width
IMAGE_HEIGHT = 2532 # roughly iPhone resolution height
BG_COLOR = (28, 28, 30) # Dark mode background gray
DOT_COLOR_ACTIVE = (255, 105, 60) # Orange
DOT_COLOR_INACTIVE = (68, 68, 70) # Dim gray
TEXT_COLOR = (255, 255, 255)
FONT_PATH = "fonts/Roboto-Regular.ttf" # Path to your uploaded font

# Grid configuration
GRID_COLS = 15
GRID_ROWS = 25
DOT_RADIUS = 18
DOT_PADDING = 22 # Space between dots

# --- Date Calculations ---
now = datetime.datetime.utcnow()
current_year = now.year
is_leap = calendar.isleap(current_year)
total_days_in_year = 366 if is_leap else 365
current_day_of_year = now.timetuple().tm_yday

days_left = total_days_in_year - current_day_of_year

print(f"Generating image for Day {current_day_of_year} of {total_days_in_year}. Days left: {days_left}")

# --- Image Generation ---

# 1. Create background
img = Image.new('RGB', (IMAGE_WIDTH, IMAGE_HEIGHT), color=BG_COLOR)
draw = ImageDraw.Draw(img)

# Load fonts
try:
    font_large = ImageFont.truetype(FONT_PATH, 240)
    font_small = ImageFont.truetype(FONT_PATH, 40)
except IOError:
    print("ERROR: Font file not found. Please ensure fonts/Roboto-Regular.ttf exists.")
    exit(1)

# 2. Draw "Fake" Time at top (Just for aesthetics to match the reference image)
time_text = "12:00"
# Calculate width to center it
bbox = draw.textbbox((0, 0), time_text, font=font_large)
text_width = bbox[2] - bbox[0]
draw.text(((IMAGE_WIDTH - text_width) / 2, 200), time_text, font=font_large, fill=TEXT_COLOR)


# 3. Draw the Grid of Dots
# Calculate total grid size to center it
total_grid_width = (GRID_COLS * (DOT_RADIUS * 2)) + ((GRID_COLS - 1) * DOT_PADDING)
total_grid_height = (GRID_ROWS * (DOT_RADIUS * 2)) + ((GRID_ROWS - 1) * DOT_PADDING)

start_x = (IMAGE_WIDTH - total_grid_width) // 2
start_y = (IMAGE_HEIGHT - total_grid_height) // 2 + 100 # slightly offset downwards

dot_count = 0
for row in range(GRID_ROWS):
    for col in range(GRID_COLS):
        dot_count += 1
        
        # Stop if we exceed total days in the year (e.g., if grid is 400 but year is 365)
        if dot_count > total_days_in_year:
            break

        # Determine color based on whether the day has passed
        if dot_count <= current_day_of_year:
            color = DOT_COLOR_ACTIVE
        else:
            color = DOT_COLOR_INACTIVE

        # Calculate position
        x = start_x + col * (DOT_RADIUS * 2 + DOT_PADDING)
        y = start_y + row * (DOT_RADIUS * 2 + DOT_PADDING)

        # Draw circle
        draw.ellipse((x, y, x + DOT_RADIUS * 2, y + DOT_RADIUS * 2), fill=color)

# 4. Draw Bottom Text
bottom_text = f"{days_left}d left"
# Center the text at the bottom
bbox_small = draw.textbbox((0, 0), bottom_text, font=font_small)
small_text_width = bbox_small[2] - bbox_small[0]
# Position near the bottom
draw.text(((IMAGE_WIDTH - small_text_width) / 2, IMAGE_HEIGHT - 200), bottom_text, font=font_small, fill=DOT_COLOR_ACTIVE)

# --- Save ---
output_filename = "daily_status.png"
img.save(output_filename)
print(f"Successfully saved {output_filename}")