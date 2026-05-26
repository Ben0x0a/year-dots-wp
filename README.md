![Wallpaper Update](https://github.com/Ben0x0a/year-dots-wp/actions/workflows/update_wallpaper.yml/badge.svg)

# Year Progress Wallpaper

A small GitHub Actions automation that generates a dynamic iPhone wallpaper every day. The wallpaper shows one dot for each day of the current year, grouped as two weeks per row, with today's dot highlighted.

Inspired by the original [t0k3n0/year](https://github.com/t0k3n0/year) repository.

## Features
* **Year Progress:** A daily updated grid of the current year, highlighting today in orange.
* **Calendar Alignment:** Rows start on Monday, with week numbers shown subtly on the left.
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
1. Open `generate_year_wallpaper.py`.
2. Find this line near the top:
    ```python
    SCREEN_SIZE = (1206, 2622)
    ```
3. Change it to your device's resolution:
    * **iPhone 17:** `(1206, 2622)`
    * **iPhone 14/15/16 Pro Max:** `(1290, 2796)`
    * **iPhone 13/14 Pro Max:** `(1284, 2778)`
    * **iPhone 11 / XR:** `(828, 1792)`
    * **iPhone 12 / 13 Mini:** `(1080, 2340)`

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
