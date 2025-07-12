#!/usr/bin/env python3
"""
Intel CPU Scraper

This script uses requests and BeautifulSoup to scrape CPU names and their associated TDP values
from the Intel ARK website using the advanced filter search URL.

uv run pip install beautifulsoup4
uv run python intel_cpu_scrapper.py

"""

import csv
import os
import re
import time

import requests
from bs4 import BeautifulSoup


class IntelCpuScraper:
    """Scraper for Intel CPU data from ARK website."""

    def __init__(self):
        """Initialize the scraper."""
        self.base_url = "https://www.intel.com/libs/apps/intel/support/ark/advancedFilterSearch?productType=873&3_MaxTDP-Min=0.03&3_MaxTDP-Max=500&forwardPath=/content/www/us/en/ark/featurefilter.html&pageNo={page_num}&sort=&sortType="
        self.results = []
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    def fetch_page(self, page_num):
        """Fetch a single page of results."""
        url = self.base_url.format(page_num=page_num)
        print(f"Fetching URL: {url}")
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()  # Raise an exception for bad status codes
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"Error fetching page {page_num}: {e}")
            return None

    def parse_html(self, html_content):
        """Parse HTML content to extract CPU data."""
        soup = BeautifulSoup(html_content, "html.parser")
        # Prioritize rows with 'data-product-id' as they are likely the CPU entries
        rows = soup.find_all("tr", {"data-product-id": True})

        if not rows:
            no_results_message = soup.find("div", class_="no-results-message")
            if (
                no_results_message
                and "no results found" in no_results_message.text.lower()
            ):
                print("No results found on this page (no-results-message).")
                return []
            if "No products matching your selection were found" in html_content:
                print("No results found on this page (No products matching text).")
                return []
            print("No CPU data rows with 'data-product-id' found on the page.")
            return None  # Indicate an issue or unexpected structure if no specific "no results" message

        page_results = []
        for row in rows:
            try:
                # Get all direct child <td> elements of the row
                tds = row.find_all("td", recursive=False)

                # Expected columns: Name, Launch, Cores, Max Turbo, Base Freq, Cache, TDP
                if len(tds) < 7:
                    # print(f"Skipping row, expected at least 7 columns, got {len(tds)}.")
                    continue

                # 1. Product Name
                cpu_name_tag = tds[0].find("a")
                if not cpu_name_tag:
                    # print("Skipping row: CPU name tag not found in first cell.")
                    continue
                cpu_name = cpu_name_tag.text.strip()

                # Helper to get text from a td cell
                def get_cell_text(cell_index, tds):
                    if cell_index < len(tds) and tds[cell_index]:
                        return tds[cell_index].text.strip()
                    return ""

                # 2. Launch Date (e.g., "Q2'25")
                launch_date = get_cell_text(1, tds)

                # 3. Total Cores (e.g., "40")
                total_cores = get_cell_text(2, tds)

                # 4. Max Turbo Frequency (e.g., "3.5 GHz")
                max_turbo_frequency = get_cell_text(3, tds)

                # 5. Processor Base Frequency (e.g., "2.5 GHz")
                processor_base_frequency = get_cell_text(4, tds)

                # 6. Cache (e.g., "160 MB")
                cache = get_cell_text(5, tds)

                # 7. TDP (e.g., "235 W")
                tdp_text_content = get_cell_text(6, tds)
                tdp_data_value = (
                    tds[6].get("data-value") if len(tds) > 6 and tds[6] else None
                )

                tdp_numeric = None
                if tdp_data_value and tdp_data_value.replace(".", "", 1).isdigit():
                    tdp_numeric = float(tdp_data_value)
                elif "W" in tdp_text_content:
                    tdp_match = re.search(r"([\\d.]+)\\s*W", tdp_text_content)
                    if tdp_match:
                        tdp_numeric = float(tdp_match.group(1))

                if not cpu_name:  # Basic validation
                    # print("Skipping row: CPU name is empty.")
                    continue

                result_item = {
                    "cpu_name": cpu_name,
                    "launch_date": launch_date,
                    "total_cores": total_cores,
                    "max_turbo_frequency": max_turbo_frequency,
                    "processor_base_frequency": processor_base_frequency,
                    "cache": cache,
                    "tdp": (
                        tdp_numeric if tdp_numeric is not None else ""
                    ),  # Store numeric TDP in Watts
                }
                page_results.append(result_item)
                # print(f"Processed: {cpu_name}, TDP: {tdp_numeric if tdp_numeric is not None else 'N/A'}")

            except Exception as e:
                print(f"Error parsing a row: {e}")
                # print(f"Problematic row HTML snippet: {str(row)[:500]}")
        return page_results

    def scrape_all_cpus(self):
        """Scrape all CPU data by iterating through pages."""
        page_num = 1
        consecutive_empty_pages = 0  # To detect end of results
        max_consecutive_empty = (
            2  # Stop after 2 consecutive pages with no new valid entries
        )

        while True:
            print(f"Processing page {page_num}...")
            html_content = self.fetch_page(page_num)

            if html_content is None:
                print(f"Failed to fetch page {page_num} after retries. Stopping.")
                break

            page_results = self.parse_html(html_content)

            if page_results is None:  # Indicates an unexpected page structure or error
                print(
                    f"Could not parse data from page {page_num} or unexpected structure. Stopping."
                )
                break

            if not page_results:
                consecutive_empty_pages += 1
                print(
                    f"No results extracted from page {page_num}. Consecutive empty pages: {consecutive_empty_pages}"
                )
                if consecutive_empty_pages >= max_consecutive_empty:
                    print("Reached max consecutive empty pages. Assuming end of data.")
                    break
            else:
                consecutive_empty_pages = 0  # Reset counter if we found data
                new_cpus_found_on_page = 0
                for res in page_results:
                    if (
                        res not in self.results
                    ):  # Avoid duplicates if any page re-processing happens
                        self.results.append(res)
                        new_cpus_found_on_page += 1
                print(
                    f"Added {new_cpus_found_on_page} new CPUs from page {page_num}. Total CPUs: {len(self.results)}"
                )
                if new_cpus_found_on_page == 0 and len(page_results) > 0:
                    # This means all CPUs on this page were duplicates, could be an issue or end of new data
                    print(
                        f"All {len(page_results)} CPUs on page {page_num} are duplicates. Considering this as end of new data."
                    )
                    break

            page_num += 1
            time.sleep(1)  # Be respectful to the server

        print(f"Scraping complete. Found {len(self.results)} CPUs.")

    def save_to_csv(self, filename="intel_cpu_ark_dataset.csv"):
        """Save the scraped data to a CSV file."""
        filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
        if not self.results:
            print("No data to save to CSV.")
            return

        keys = self.results[0].keys()
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(self.results)
        print(f"Data saved to {filepath}")


def main():
    """Main function to run the scraper."""
    scraper = IntelCpuScraper()
    scraper.scrape_all_cpus()

    if scraper.results:
        scraper.save_to_csv()
    else:
        print("No data was scraped.")


if __name__ == "__main__":
    main()


"""

Sample content from the Intel ARK page:

Product Name
Launch Date
Total Cores
Max Turbo Frequency
Processor Base Frequency
Cache
TDP

                                    <tr class="blank-table-row   seg-server  seg-embedded  "
                                        data-codename="Granite Rapids-D"
                                        data-filter="Server"
                                        data-product-id="242908">
                                        <td class="ark-product-name ark-accessible-color component"
                                            data-value="4" data-component="arkproductlink"
                                            data-component-id="1">
                                            <div class="add-compare-wrap">
                                                <label class="containerCB component" data-component="wa_skip_track"
                                                    data-component-id="1">
                                                    <input class="compare-checkbox compare-toggle"
                                                        data-component="ark-component"
                                                        data-product-id="242908" type="checkbox">
                                                    <span class="checkmark"></span>
                                                </label>
                                                <a href="/content/www/us/en/products/sku/242908/intel-xeon-6716pb-processor-160m-cache-2-50-ghz/specifications.html">Intel® Xeon® 6716P-B Processor</a>
                                            </div>
                                        </td>

                                                <td class=""
                                                    data-value="">
                                                                Q2'25
                                                </td>
                                                <td class=""
                                                    data-value="40">

                                                                40
                                                </td>
                                                <td class=""
                                                    data-value="3500">
                                                                3.5 GHz
                                                </td>
                                                <td class=""
                                                    data-value="2500">
                                                                2.5 GHz
                                                </td>
                                                <td class=""
                                                    data-value="163840">
                                                                160 MB
                                                </td>
                                                <td class=""
                                                    data-value="235">
                                                                235 W
                                                </td>
                                    </tr>
"""
