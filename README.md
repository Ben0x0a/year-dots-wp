![Wallpaper Update](https://github.com/Ben0x0a/year-dots-wp/actions/workflows/update_wallpaper.yml/badge.svg)

# Year Progress Wallpaper

A small GitHub Actions automation that generates a dynamic iPhone wallpaper every day. The wallpaper shows one dot for each day of the current year, grouped as two weeks per row, with today's dot highlighted.

Inspired by the original [t0k3n0/year](https://github.com/t0k3n0/year) repository.

## Features
* **Year Progress:** A daily updated grid of the current year, highlighting today.
* **Calendar Alignment:** Rows start on Monday, with week numbers shown subtly on the left.
* **YAML Settings:** Layout, colors, spacing, text position, and deadline markers can be edited in `settings.yaml`.
* **Zero Battery Drain:** The image is rendered by GitHub Actions; your phone only downloads the final PNG.

## Setup Guide

### 1. Fork this Repository
Click the **Fork** button to create your own copy of this project.

### 2. Activate the Generator
1. Go to the **Actions** tab.
2. Click **Update Wallpapers** on the left.
3. Click **Run workflow** to generate your first image.

## Customizing for Your Phone

The default resolution is set for **iPhone 17** (`1206 x 2622`). The raw GitHub image URL serves a static PNG, so query parameters like `?resolution=...` cannot make GitHub Actions render a different size on demand. If you use another phone, update the resolution before the workflow runs.

### How to Change Resolution
1. Open `settings.yaml`.
2. Change:
    ```yaml
    screen:
      width: 1206
      height: 2622
    ```
3. Use your device's resolution:
    * **iPhone 17:** `(1206, 2622)`
    * **iPhone 14/15/16 Pro Max:** `(1290, 2796)`
    * **iPhone 13/14 Pro Max:** `(1284, 2778)`
    * **iPhone 11 / XR:** `(828, 1792)`
    * **iPhone 12 / 13 Mini:** `(1080, 2340)`

### YAML Settings

Most visual settings live in `settings.yaml`:

```yaml
layout:
  center_position: [603, 1540]
  horizontal_spacing_percent: 0.013
  vertical_spacing_percent: 0.013
  week_label_position: left
  status_text_position: top
  status_text_max_width_percent: 0.9
  next_year_deadline_notice:
    enabled: true
    days_before_year_end: 50
    deadline_window_days: 50
```

`center_position` is the center of the dot grid. Week label space is reserved symmetrically around the grid, so switching `week_label_position` between `left`, `right`, and `both` does not move the dots.

Left labels show odd week numbers such as `1, 3, 5`; right labels show even week numbers such as `2, 4, 6`. To move the grid lower, increase the second number in `center_position`. To move the status text under the grid, set `status_text_position: bottom`.

### Deadline Dots

Add dates to `deadlines` to color those dots. They do not add text labels. Only upcoming occurrences in the current year are shown; past occurrences are ignored.

```yaml
deadlines:
  - date: 2026-09-30
    color: "#f5b642"
  - date: 2026-12-15
    color: [210, 70, 90]
```

Recurring deadlines use `date` as the first occurrence and support `yearly`, `semester` / `semestre`, `trimester` / `trimestre`, and `monthly`.

```yaml
deadlines:
  - date: 2026-01-02
    recurrence: yearly
    color: "#f5b642"
  - date: 2026-03-15
    recurrence: semestre
    color: "#5eb5ff"
  - date: 2026-04-10
    recurrence: trimestre
    color: "#d776ff"
  - date: 2026-05-01
    recurrence: monthly
    color: "#ff6f61"
```

When `layout.next_year_deadline_notice.enabled` is `true`, the wallpaper adds a small grey notice during the last configured days of the year if a deadline occurs in the first configured days of the next year. Example text:

```text
1st deadline of 2027 on Jan 2nd.
```

## iOS Shortcut Setup

Create a shortcut with:

1. **Get Contents of URL**
2. Paste your raw image link:
    ```text
    https://raw.githubusercontent.com/<YOUR_USERNAME>/year-dots-wp/generated/year_progress.png
    ```
    Replace `<YOUR_USERNAME>` with your GitHub username. If you rename the forked repository, replace `year-dots-wp` with your repository name. If your default branch is not `main`, replace `main` with your branch name.
3. Open the URL in a browser once after the workflow has run. It should display the generated PNG directly.
4. **Get Image from Input**
5. **Set Wallpaper** with "Show Preview" turned off
6. Set an Automation to run this daily

## Android Setup

Use any wallpaper app that can fetch a remote image URL on a schedule, such as [Remote Wallpaper](https://github.com/cssnr/remote-wallpaper-android/releases), Muzei with a URL source, or MacroDroid.
