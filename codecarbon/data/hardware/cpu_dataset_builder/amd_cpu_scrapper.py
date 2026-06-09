"""
This script uses Playwright to scrape AMD CPU data from their website and save it as a CSV file.

uv run pip install playwright
uv run python amd_cpu_scrapper.py
"""

import asyncio

from playwright.async_api import Page, async_playwright


async def handle_cookie_banner(page: Page):
    """Attempts to find and click a 'Reject All' button for cookie consent."""
    try:
        reject_button_selectors = [
            "button:has-text('Reject All')",
            "button:has-text('Decline All')",
            "button[id*='reject']",
            "button[class*='reject']",
            "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'reject all')]",
            "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'decline all')]",
        ]

        reject_button = None
        for selector in reject_button_selectors:
            try:
                button = page.locator(selector).first
                if await button.is_visible(
                    timeout=2000
                ):  # Short timeout for visibility check
                    reject_button = button
                    print(f"Found cookie consent button with selector: {selector}")
                    break
            except Exception:
                pass  # Selector not found or button not visible, try next

        if reject_button:
            await reject_button.click()
            print("Clicked 'Reject All' on cookie banner.")
            await page.wait_for_timeout(1000)  # Wait a bit for the banner to disappear
        else:
            print(
                "Cookie banner 'Reject All' button not found or not visible after trying common selectors."
            )

    except Exception as cookie_error:
        print(f"Could not handle cookie banner: {cookie_error}")


async def download_csv_from_url(page: Page, url: str, output_filename: str):
    """Navigates to a URL, handles cookie banner, and downloads a CSV file."""
    print(f"Attempting to download from: {url}")
    retries = 2
    for attempt in range(retries):
        try:
            await page.goto(url, timeout=30000)  # Increased timeout for page load
            await handle_cookie_banner(page)
            break  # If goto is successful, break the loop
        except Exception as e:
            print(f"Attempt {attempt + 1} to navigate to {url} failed: {e}")
            if attempt < retries - 1:
                await asyncio.sleep(5)  # Wait for 5 seconds before retrying
            else:
                print(f"All retries failed for {url}.")
                return  # Exit if all retries fail

    try:
        # Wait for the download to start after clicking the button
        async with page.expect_download(
            timeout=30000
        ) as download_info:  # Increased timeout for download
            # Click the button with the class "buttons-csv"
            await page.locator(".buttons-csv").click()
            print(f"Clicked download button for {url}")

        download = await download_info.value

        # Save the downloaded file
        file_path = f"{output_filename}"
        await download.save_as(file_path)
        print(f"File downloaded from {url} and saved as {file_path}")

    except Exception as e:
        print(f"An error occurred while downloading from {url}: {e}")


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,  # Set to True for production
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
            ],
        )
        page = await browser.new_page()

        urls_to_download = [
            {
                "url": "https://www.amd.com/en/products/specifications/server-processor.html",
                "filename": "amd_cpu_server_dataset.csv",
            },
            {
                "url": "https://www.amd.com/en/products/specifications/processors.html",
                "filename": "amd_cpu_desktop_dataset.csv",
            },
        ]

        for item in urls_to_download:
            await download_csv_from_url(page, item["url"], item["filename"])
            await asyncio.sleep(2)  # Small delay between downloads

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
