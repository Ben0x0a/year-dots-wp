from PIL import Image, ImageDraw, ImageFont
from datetime import date, timedelta
import calendar
import argparse
import copy
import math
import os
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

DEFAULT_CONFIG = {
    "output_filename": "year_progress.png",
    "screen": {
        "width": 1206,
        "height": 2622,
    },
    "colors": {
        "background": [20, 20, 20],
        "past": [80, 80, 80],
        "future": [40, 40, 40],
        "today": [36, 195, 0],
        "text": [200, 200, 200],
        "week_label": [95, 95, 95],
        "deadline_notice": [95, 95, 95],
    },
    "layout": {
        "center_position": [603, 1540],
        "columns": 14,
        "dot_radius_percent": 0.012,
        "horizontal_spacing_percent": 0.013,
        "vertical_spacing_percent": 0.013,
        "week_gap_percent": 0.03,
        "week_label_offset_percent": 0.032,
        "week_label_position": "left",
        "status_text_position": "top",
        "status_text_gap_percent": 0.075,
        "status_text_font_percent": 0.035,
        "status_text_min_font_percent": 0.025,
        "status_text_max_width_percent": 0.9,
        "week_label_font_percent": 0.025,
        "next_year_deadline_notice": {
            "enabled": True,
            "days_before_year_end": 50,
            "deadline_window_days": 50,
            "gap_percent": 0.02,
            "font_percent": 0.024,
            "min_font_percent": 0.018,
            "max_width_percent": 0.9,
        },
    },
    "deadlines": [],
}

RECURRENCE_MONTHS = {
    "monthly": 1,
    "mensualy": 1,
    "mensually": 1,
    "month": 1,
    "trimester": 3,
    "trimestre": 3,
    "quarterly": 3,
    "quarter": 3,
    "semester": 6,
    "semestre": 6,
    "semiannual": 6,
    "semiannually": 6,
    "yearly": 12,
    "yealry": 12,
    "annual": 12,
    "annually": 12,
}

def deep_merge(base, override):
    if override is None:
        return copy.deepcopy(base)
    if not isinstance(base, dict) or not isinstance(override, dict):
        return copy.deepcopy(override)
    merged = copy.deepcopy(base)
    for key, value in override.items():
        merged[key] = deep_merge(merged.get(key), value)
    return merged


def strip_yaml_comment(line):
    in_single_quote = False
    in_double_quote = False
    for index, character in enumerate(line):
        if character == "'" and not in_double_quote:
            in_single_quote = not in_single_quote
        elif character == '"' and not in_single_quote:
            in_double_quote = not in_double_quote
        elif character == "#" and not in_single_quote and not in_double_quote:
            return line[:index].rstrip()
    return line.rstrip()


def split_inline_list(value):
    items = []
    current = []
    in_single_quote = False
    in_double_quote = False
    for character in value:
        if character == "'" and not in_double_quote:
            in_single_quote = not in_single_quote
        elif character == '"' and not in_single_quote:
            in_double_quote = not in_double_quote
        elif character == "," and not in_single_quote and not in_double_quote:
            items.append("".join(current).strip())
            current = []
            continue
        current.append(character)
    items.append("".join(current).strip())
    return items


def parse_yaml_scalar(value):
    value = value.strip()
    if value == "":
        return ""
    if value in {"[]", "{}"}:
        return [] if value == "[]" else {}
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [parse_yaml_scalar(item) for item in split_inline_list(inner)]
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    if value.lower() in {"null", "none"}:
        return None
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value


def parse_simple_yaml_mapping(content):
    key, value = content.split(":", 1)
    key = key.strip()
    value = value.strip()
    if not key:
        raise ValueError("YAML keys cannot be empty")
    return key, parse_yaml_scalar(value) if value else None


def parse_simple_yaml_block(lines, index, indent):
    if index >= len(lines):
        return {}, index
    current_indent, content = lines[index]
    if current_indent < indent:
        return {}, index
    if current_indent != indent:
        raise ValueError("Invalid YAML indentation")

    if content.startswith("- "):
        result = []
        while index < len(lines) and lines[index][0] == indent and lines[index][1].startswith("- "):
            item_content = lines[index][1][2:].strip()
            index += 1
            if not item_content:
                item_value, index = parse_simple_yaml_block(lines, index, indent + 2)
                result.append(item_value)
                continue
            if ":" in item_content:
                key, value = parse_simple_yaml_mapping(item_content)
                item_value = {key: value}
                if value is None:
                    nested_value, index = parse_simple_yaml_block(lines, index, indent + 2)
                    item_value[key] = nested_value
                elif index < len(lines) and lines[index][0] > indent:
                    nested_value, index = parse_simple_yaml_block(lines, index, indent + 2)
                    if isinstance(nested_value, dict):
                        item_value.update(nested_value)
                    else:
                        raise ValueError("List item continuation must be a mapping")
                result.append(item_value)
            else:
                result.append(parse_yaml_scalar(item_content))
        return result, index

    result = {}
    while index < len(lines) and lines[index][0] == indent and not lines[index][1].startswith("- "):
        key, value = parse_simple_yaml_mapping(lines[index][1])
        index += 1
        if value is None:
            value, index = parse_simple_yaml_block(lines, index, indent + 2)
        result[key] = value
    return result, index


def load_simple_yaml(text):
    lines = []
    for raw_line in text.splitlines():
        line = strip_yaml_comment(raw_line)
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        if indent % 2 != 0:
            raise ValueError("YAML indentation must use two spaces")
        lines.append((indent, line.strip()))
    if not lines:
        return {}
    result, index = parse_simple_yaml_block(lines, 0, lines[0][0])
    if index != len(lines):
        raise ValueError("Could not parse all YAML settings")
    return result


def load_config(config_path):
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with path.open("r", encoding="utf-8") as config_file:
        if yaml is not None:
            user_config = yaml.safe_load(config_file) or {}
        else:
            user_config = load_simple_yaml(config_file.read())
    return deep_merge(DEFAULT_CONFIG, user_config)


def parse_color(value, setting_name):
    if isinstance(value, str):
        hex_value = value.strip().lstrip("#")
        if len(hex_value) != 6:
            raise ValueError(f"{setting_name} must be #RRGGBB or three RGB numbers")
        try:
            return tuple(int(hex_value[index:index + 2], 16) for index in (0, 2, 4))
        except ValueError as exc:
            raise ValueError(f"{setting_name} must be #RRGGBB or three RGB numbers") from exc
    if isinstance(value, (list, tuple)) and len(value) == 3:
        color = tuple(int(channel) for channel in value)
        if all(0 <= channel <= 255 for channel in color):
            return color
    raise ValueError(f"{setting_name} must be #RRGGBB or three RGB numbers")


def parse_date(value, setting_name):
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError as exc:
            raise ValueError(f"{setting_name} must use YYYY-MM-DD") from exc
    raise ValueError(f"{setting_name} must use YYYY-MM-DD")


def normalize_recurrence(value, setting_name):
    if value is None:
        return None
    recurrence = str(value).strip().lower()
    if recurrence in {"", "none", "once", "one-time", "single"}:
        return None
    if recurrence not in RECURRENCE_MONTHS:
        supported = ", ".join(sorted(RECURRENCE_MONTHS))
        raise ValueError(f"{setting_name} must be one of: {supported}")
    return recurrence


def add_months(source_date, months):
    month_index = (source_date.month - 1) + months
    year = source_date.year + (month_index // 12)
    month = (month_index % 12) + 1
    day = min(source_date.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def iter_deadline_occurrences(start_date, recurrence, window_start, window_end):
    if recurrence is None:
        if window_start <= start_date <= window_end:
            yield start_date
        return

    months = RECURRENCE_MONTHS[recurrence]
    occurrence_index = 0
    current_date = start_date
    while current_date < window_start:
        occurrence_index += 1
        current_date = add_months(start_date, months * occurrence_index)
    while current_date <= window_end:
        yield current_date
        occurrence_index += 1
        current_date = add_months(start_date, months * occurrence_index)


def collect_deadline_occurrences(config, window_start, window_end):
    occurrences = []
    for index, deadline in enumerate(config.get("deadlines", []), start=1):
        if not isinstance(deadline, dict):
            raise ValueError(f"deadlines[{index}] must contain date and color")
        start_date = parse_date(deadline.get("date"), f"deadlines[{index}].date")
        recurrence = normalize_recurrence(deadline.get("recurrence"), f"deadlines[{index}].recurrence")
        deadline_color = parse_color(deadline.get("color"), f"deadlines[{index}].color")
        for occurrence_date in iter_deadline_occurrences(start_date, recurrence, window_start, window_end):
            occurrences.append({
                "date": occurrence_date,
                "color": deadline_color,
                "index": index,
            })
    return sorted(occurrences, key=lambda occurrence: (occurrence["date"], occurrence["index"]))


def collect_deadline_colors(config, today, year):
    deadline_colors = {}
    window_start = today + timedelta(days=1)
    window_end = date(year, 12, 31)
    for occurrence in collect_deadline_occurrences(config, window_start, window_end):
        deadline_colors[occurrence["date"]] = occurrence["color"]
    return deadline_colors


def ordinal_number(value):
    if 10 <= value % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(value % 10, "th")
    return f"{value}{suffix}"


def format_month_day_words(value):
    return f"{value.strftime('%b')} {ordinal_number(value.day)}"


def build_next_year_deadline_notice(config, today):
    notice_config = config["layout"]["next_year_deadline_notice"]
    if not notice_config["enabled"]:
        return None

    current_year_end = date(today.year, 12, 31)
    days_before_year_end = max(1, int(notice_config["days_before_year_end"]))
    notice_start = current_year_end - timedelta(days=days_before_year_end - 1)
    if today < notice_start:
        return None

    next_year = today.year + 1
    window_start = date(next_year, 1, 1)
    deadline_window_days = max(1, int(notice_config["deadline_window_days"]))
    window_end = window_start + timedelta(days=deadline_window_days - 1)
    occurrences = collect_deadline_occurrences(config, window_start, window_end)
    if not occurrences:
        return None

    first_occurrence = occurrences[0]["date"]
    return (
        f"{ordinal_number(1)} deadline of {next_year} "
        f"on {format_month_day_words(first_occurrence)}."
    )


def get_screen_size(config):
    screen = config["screen"]
    return int(screen["width"]), int(screen["height"])


def scaled_size(screen_size, percent_of_width):
    return max(1, round(min(screen_size) * percent_of_width))

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

def select_status_font(draw, screen_size, layout, left_text, right_text):
    max_text_width = screen_size[0] * layout["status_text_max_width_percent"]
    font_main = load_font(scaled_size(screen_size, layout["status_text_font_percent"]))
    start_size = scaled_size(screen_size, layout["status_text_font_percent"])
    min_size = scaled_size(screen_size, layout["status_text_min_font_percent"])
    for font_size in range(start_size, min_size, -2):
        font_main = load_font(font_size)
        left_box = draw.textbbox((0, 0), left_text, font=font_main)
        right_box = draw.textbbox((0, 0), right_text, font=font_main)
        left_width = left_box[2] - left_box[0]
        right_width = right_box[2] - right_box[0]
        if left_width + right_width <= max_text_width:
            break
    return font_main


def select_single_line_font(draw, screen_size, text, font_percent, min_font_percent, max_width_percent):
    max_text_width = screen_size[0] * max_width_percent
    font_main = load_font(scaled_size(screen_size, font_percent))
    start_size = scaled_size(screen_size, font_percent)
    min_size = scaled_size(screen_size, min_font_percent)
    for font_size in range(start_size, min_size, -2):
        font_main = load_font(font_size)
        text_box = draw.textbbox((0, 0), text, font=font_main)
        text_width = text_box[2] - text_box[0]
        if text_width <= max_text_width:
            break
    return font_main


def measure_status_text(draw, font_main, left_text, right_text):
    left_box = draw.textbbox((0, 0), left_text, font=font_main)
    right_box = draw.textbbox((0, 0), right_text, font=font_main)
    left_width = left_box[2] - left_box[0]
    right_width = right_box[2] - right_box[0]
    left_height = left_box[3] - left_box[1]
    right_height = right_box[3] - right_box[1]
    return left_width, right_width, max(left_height, right_height)


def measure_single_line_text(draw, font_main, text):
    text_box = draw.textbbox((0, 0), text, font=font_main)
    return text_box[2] - text_box[0], text_box[3] - text_box[1]


def draw_status_text(draw, center_x, y, left_text, right_text, colors, font_main):
    left_width, right_width, _ = measure_status_text(draw, font_main, left_text, right_text)
    text_x = center_x - ((left_width + right_width) / 2)
    draw.text((text_x, y), left_text, fill=colors["today"], font=font_main, anchor="lt")
    draw.text((text_x + left_width, y), right_text, fill=colors["text"], font=font_main, anchor="lt")


def draw_centered_text(draw, center_x, y, text, color, font_main):
    text_width, _ = measure_single_line_text(draw, font_main, text)
    draw.text((center_x - (text_width / 2), y), text, fill=color, font=font_main, anchor="lt")


def normalize_week_label_position(value):
    week_label_position = str(value).strip().lower()
    if week_label_position not in {"left", "right", "both"}:
        raise ValueError("layout.week_label_position must be 'left', 'right', or 'both'")
    return week_label_position


def row_half_has_year_day(row, start_col, end_col, layout, first_day, year):
    for col in range(start_col, end_col):
        cell_index = (row * layout["cols"]) + col
        day_offset = cell_index - layout["leading_empty_days"]
        current_date = first_day + timedelta(days=day_offset)
        if current_date.year == year:
            return True
    return False


def build_layout(draw, config, today, total_days, first_day, next_year_deadline_notice):
    screen_size = get_screen_size(config)
    layout = config["layout"]
    cols = int(layout["columns"])
    leading_empty_days = first_day.weekday()
    rows = math.ceil((leading_empty_days + total_days) / cols)

    dot_radius = scaled_size(screen_size, layout["dot_radius_percent"])
    dot_size = dot_radius * 2
    horizontal_gap = scaled_size(screen_size, layout["horizontal_spacing_percent"])
    vertical_gap = scaled_size(screen_size, layout["vertical_spacing_percent"])
    week_gap = scaled_size(screen_size, layout["week_gap_percent"])
    week_label_offset = scaled_size(screen_size, layout["week_label_offset_percent"])

    grid_width = (cols * dot_size) + ((cols - 1) * horizontal_gap) + week_gap
    grid_height = (rows * dot_size) + ((rows - 1) * vertical_gap)

    font_label = load_font(scaled_size(screen_size, layout["week_label_font_percent"]), bold=True)
    week_label_width = 0
    for row in range(rows):
        left_week_number = (row * 2) + 1
        right_week_number = (row * 2) + 2
        for week_number in (left_week_number, right_week_number):
            label_box = draw.textbbox((0, 0), str(week_number), font=font_label)
            week_label_width = max(week_label_width, label_box[2] - label_box[0])

    days_left = total_days - today.timetuple().tm_yday
    percent_done = int((today.timetuple().tm_yday / total_days) * 100)
    if days_left == 0:
        left_text = "Last day of the year"
    else:
        day_label = "day" if days_left == 1 else "days"
        left_text = f"{days_left} {day_label} left"
    right_text = f" · {percent_done}% completed"

    font_main = select_status_font(draw, screen_size, layout, left_text, right_text)
    _, _, status_text_height = measure_status_text(draw, font_main, left_text, right_text)
    status_text_gap = scaled_size(screen_size, layout["status_text_gap_percent"])
    notice_font = None
    notice_height = 0
    notice_gap = 0
    if next_year_deadline_notice:
        notice_config = layout["next_year_deadline_notice"]
        notice_font = select_single_line_font(
            draw,
            screen_size,
            next_year_deadline_notice,
            notice_config["font_percent"],
            notice_config["min_font_percent"],
            notice_config["max_width_percent"],
        )
        _, notice_height = measure_single_line_text(draw, notice_font, next_year_deadline_notice)
        notice_gap = scaled_size(screen_size, notice_config["gap_percent"])
    status_block_height = status_text_height
    if next_year_deadline_notice:
        status_block_height += notice_gap + notice_height

    status_text_position = str(layout["status_text_position"]).lower()
    if status_text_position not in {"top", "bottom"}:
        raise ValueError("layout.status_text_position must be 'top' or 'bottom'")
    week_label_position = normalize_week_label_position(layout["week_label_position"])

    center_x, center_y = [int(value) for value in layout["center_position"]]

    start_x = center_x - (grid_width / 2)
    start_y = center_y - (grid_height / 2)
    if status_text_position == "top":
        status_text_y = start_y - status_text_gap - status_block_height
        notice_text_y = status_text_y + status_text_height + notice_gap
    else:
        status_text_y = start_y + grid_height + status_text_gap
        notice_text_y = status_text_y + status_text_height + notice_gap

    return {
        "cols": cols,
        "rows": rows,
        "dot_radius": dot_radius,
        "dot_size": dot_size,
        "horizontal_gap": horizontal_gap,
        "vertical_gap": vertical_gap,
        "week_gap": week_gap,
        "week_label_offset": week_label_offset,
        "week_label_width": week_label_width,
        "week_label_position": week_label_position,
        "left_label_x": start_x - week_label_offset,
        "right_label_x": start_x + grid_width + week_label_offset,
        "start_x": start_x,
        "start_y": start_y,
        "grid_height": grid_height,
        "font_label": font_label,
        "font_main": font_main,
        "left_text": left_text,
        "right_text": right_text,
        "status_text_y": status_text_y,
        "notice_text": next_year_deadline_notice,
        "notice_text_y": notice_text_y,
        "notice_font": notice_font,
        "figure_center_x": center_x,
        "leading_empty_days": leading_empty_days,
    }


def create_year_wallpaper(config):
    today = date.today()
    year = today.year
    is_leap = calendar.isleap(year)
    total_days = 366 if is_leap else 365
    first_day = date(year, 1, 1)

    screen_size = get_screen_size(config)
    colors = {name: parse_color(value, f"colors.{name}") for name, value in config["colors"].items()}
    deadline_colors = collect_deadline_colors(config, today, year)
    next_year_deadline_notice = build_next_year_deadline_notice(config, today)

    img = Image.new('RGB', screen_size, color=colors["background"])
    draw = ImageDraw.Draw(img)
    layout = build_layout(draw, config, today, total_days, first_day, next_year_deadline_notice)

    # --- DRAW GRID ---
    for row in range(layout["rows"]):
        label_y = layout["start_y"] + row * (layout["dot_size"] + layout["vertical_gap"]) + layout["dot_radius"]
        if layout["week_label_position"] in {"left", "both"} and row_half_has_year_day(row, 0, 7, layout, first_day, year):
            draw.text(
                (layout["left_label_x"], label_y),
                str((row * 2) + 1),
                fill=colors["week_label"],
                font=layout["font_label"],
                anchor="rm",
            )
        if layout["week_label_position"] in {"right", "both"} and row_half_has_year_day(row, 7, 14, layout, first_day, year):
            draw.text(
                (layout["right_label_x"], label_y),
                str((row * 2) + 2),
                fill=colors["week_label"],
                font=layout["font_label"],
                anchor="lm",
            )

        for col in range(layout["cols"]):
            cell_index = (row * layout["cols"]) + col
            day_offset = cell_index - layout["leading_empty_days"]
            current_date = first_day + timedelta(days=day_offset)

            x = layout["start_x"] + col * (layout["dot_size"] + layout["horizontal_gap"])
            if col >= 7:
                x += layout["week_gap"]
            y = layout["start_y"] + row * (layout["dot_size"] + layout["vertical_gap"])
            
            box = [x, y, x + layout["dot_size"], y + layout["dot_size"]]
            
            if current_date < first_day or current_date.year > year:
                continue
            elif current_date < today:
                draw.ellipse(box, fill=colors["past"])
            elif current_date == today:
                draw.ellipse(box, fill=colors["today"])
            elif current_date in deadline_colors:
                draw.ellipse(box, fill=deadline_colors[current_date])
            else:
                draw.ellipse(box, fill=colors["future"])

    # --- STATUS TEXT ---
    draw_status_text(
        draw,
        layout["figure_center_x"],
        layout["status_text_y"],
        layout["left_text"],
        layout["right_text"],
        colors,
        layout["font_main"],
    )
    if layout["notice_text"]:
        draw_centered_text(
            draw,
            layout["figure_center_x"],
            layout["notice_text_y"],
            layout["notice_text"],
            colors["deadline_notice"],
            layout["notice_font"],
        )

    img.save(config["output_filename"])
    print("Year progress wallpaper generated.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a year progress wallpaper.")
    parser.add_argument("--config", default="settings.yaml", help="Path to the YAML settings file.")
    args = parser.parse_args()
    create_year_wallpaper(load_config(args.config))
