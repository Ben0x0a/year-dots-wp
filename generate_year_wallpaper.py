from PIL import Image, ImageDraw, ImageFont
from datetime import date, timedelta
import calendar
import math
import os

# --- CONFIGURATION ---
SCREEN_SIZE = (1206, 2622)     # iPhone 17 resolution
BG_COLOR = (20, 20, 20)        # Dark Charcoal
FILLED_COLOR = (80, 80, 80)    # Light Gray
EMPTY_COLOR = (40, 40, 40)     # Dark Gray
ACTIVE_COLOR = (36, 195, 0)    # Vaud green
TEXT_COLOR = (200, 200, 200)   # Light Gray labels
WEEK_LABEL_COLOR = (95, 95, 95)
STATUS_TEXT_POSITION = "top"   # "top" or "bottom"

def scaled_size(percent_of_width):
    return max(1, round(min(SCREEN_SIZE) * percent_of_width))

def load_font(size, bold=False):
    font_paths = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/HelveticaNeue.ttc",
        "/System/Library/Fonts/SFNS.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for font_path in font_paths:
        if os.path.exists(font_path):
            return ImageFont.truetype(font_path, size)
    return ImageFont.load_default()

def draw_status_text(draw, y, left_text, right_text):
    max_text_width = SCREEN_SIZE[0] * 0.9
    font_main = load_font(scaled_size(0.035))
    for font_size in range(scaled_size(0.035), scaled_size(0.025), -2):
        font_main = load_font(font_size)
        left_box = draw.textbbox((0, 0), left_text, font=font_main)
        right_box = draw.textbbox((0, 0), right_text, font=font_main)
        left_width = left_box[2] - left_box[0]
        right_width = right_box[2] - right_box[0]
        if left_width + right_width <= max_text_width:
            break

    left_box = draw.textbbox((0, 0), left_text, font=font_main)
    right_box = draw.textbbox((0, 0), right_text, font=font_main)
    left_width = left_box[2] - left_box[0]
    right_width = right_box[2] - right_box[0]
    text_x = (SCREEN_SIZE[0] - left_width - right_width) // 2
    draw.text((text_x, y), left_text, fill=ACTIVE_COLOR, font=font_main, anchor="la")
    draw.text((text_x + left_width, y), right_text, fill=TEXT_COLOR, font=font_main, anchor="la")

def create_year_wallpaper():
    today = date.today()
    year = today.year
    is_leap = calendar.isleap(year)
    total_days = 366 if is_leap else 365
    day_of_year = today.timetuple().tm_yday
    first_day = date(year, 1, 1)
    leading_empty_days = first_day.weekday()
    
    # Stats
    days_left = total_days - day_of_year
    percent_done = int((day_of_year / total_days) * 100)

    img = Image.new('RGB', SCREEN_SIZE, color=BG_COLOR)
    draw = ImageDraw.Draw(img)

    # --- GRID SETTINGS ---
    cols = 14
    rows = math.ceil((leading_empty_days + total_days) / cols)
    
    dot_radius = scaled_size(0.012)
    dot_size = dot_radius * 2
    gap = scaled_size(0.013)
    week_gap = scaled_size(0.03)
    
    # Calculate grid dimensions
    grid_width = (cols * dot_size) + ((cols - 1) * gap) + week_gap
    grid_height = (rows * dot_size) + ((rows - 1) * gap)
    
    # Center Point
    start_x = (SCREEN_SIZE[0] - grid_width) // 2
    if STATUS_TEXT_POSITION == "top":
        text_gap = scaled_size(0.075)
        start_y = ((SCREEN_SIZE[1] - grid_height) // 2) + scaled_size(0.18)
        status_text_y = start_y - text_gap
    else:
        text_gap = scaled_size(0.045)
        start_y = ((SCREEN_SIZE[1] - grid_height) // 2) + scaled_size(0.18)
        status_text_y = start_y + grid_height + text_gap

    # --- FONTS ---
    font_main = load_font(scaled_size(0.035))
    font_label = load_font(scaled_size(0.025), bold=True)

    # --- DRAW GRID ---
    for row in range(rows):
        week_number = (row * 2) + 1
        draw.text(
            (start_x - scaled_size(0.032), start_y + row * (dot_size + gap) + dot_radius),
            str(week_number),
            fill=WEEK_LABEL_COLOR,
            font=font_label,
            anchor="rm",
        )

        for col in range(cols):
            cell_index = (row * cols) + col
            day_offset = cell_index - leading_empty_days
            current_date = first_day + timedelta(days=day_offset)

            x = start_x + col * (dot_size + gap)
            if col >= 7:
                x += week_gap
            y = start_y + row * (dot_size + gap)
            
            box = [x, y, x + dot_size, y + dot_size]
            
            if current_date < first_day or current_date.year > year:
                continue
            elif current_date < today:
                draw.ellipse(box, fill=FILLED_COLOR)
            elif current_date == today:
                draw.ellipse(box, fill=ACTIVE_COLOR)
            else:
                draw.ellipse(box, fill=EMPTY_COLOR)

    # --- STATUS TEXT ---
    if days_left == 0:
        left_text = "Last day of the year"
    else:
        day_label = "day" if days_left == 1 else "days"
        left_text = f"{days_left} {day_label} left"
    right_text = f" · {percent_done}% completed"
    draw_status_text(draw, status_text_y, left_text, right_text)

    img.save("year_progress.png")
    print("Year progress wallpaper generated.")

if __name__ == "__main__":
    create_year_wallpaper()
