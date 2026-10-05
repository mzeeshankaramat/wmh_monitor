from playwright.sync_api import sync_playwright
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
import csv
import time
from pathlib import Path


URL = "https://connect.recsports.vt.edu/facilityoccupancy"

CSV_FILE = Path("wmh_occupancy.csv")


def get_wmh_occupancy():

    with sync_playwright() as p:

        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            page.goto(URL, wait_until="networkidle", timeout=60000)

            # Give the occupancy widget time to render
            page.wait_for_timeout(3000)

            result = page.evaluate("""
            () => {

                const elements = Array.from(
                    document.querySelectorAll("h1,h2,h3,h4,h5,h6,div,span")
                );

                const heading = elements.find(
                    el => el.textContent.trim() === "WMH Service Desk"
                );

                if (!heading) {
                    return null;
                }

                // Move upward until we find the container
                // containing the occupancy canvas.
                let container = heading;

                while (container) {

                    const canvas =
                        container.querySelector("canvas.occupancy-chart");

                    if (canvas && canvas.dataset.occupancy) {

                        let description = "";

                        const desc =
                            container.querySelector(".visually-hidden");

                        if (desc) {
                            description = desc.textContent.trim();
                        }

                        return {
                            occupancy: canvas.dataset.occupancy,
                            remaining: canvas.dataset.remaining,
                            ratio: canvas.dataset.ratio,
                            description: description
                        };
                    }

                    container = container.parentElement;
                }

                return null;
            }
            """)

            return result

        finally:
            browser.close()


def save_result(result):

    now = datetime.now(
        ZoneInfo("America/New_York")
    )

    timestamp = now.strftime("%Y-%m-%d %H:%M")

    if result is None:
        print(f"{timestamp} | FETCH FAILED")
        return

    occupancy = int(result["occupancy"])
    remaining = int(result["remaining"])
    ratio = float(result["ratio"])

    max_capacity = occupancy + remaining
    percent = ratio * 100

    file_exists = CSV_FILE.exists()

    with CSV_FILE.open("a", newline="") as f:

        writer = csv.writer(f)

        if not file_exists:
            writer.writerow([
                "timestamp",
                "occupancy",
                "occupancy_percent",
                "remaining",
                "max_capacity"
            ])

        writer.writerow([
            timestamp,
            occupancy,
            round(percent, 1),
            remaining,
            max_capacity
        ])

    print(
        f"{timestamp} | "
        f"{occupancy} | "
        f"{percent:.1f}% | "
        f"{remaining} remaining"
    )


def main():

    # Retry up to three times
    for attempt in range(3):

        try:
            result = get_wmh_occupancy()

            if result:
                save_result(result)
                return

        except Exception as e:
            print(
                f"Attempt {attempt + 1} failed:",
                e
            )

        time.sleep(10)

    save_result(None)


if __name__ == "__main__":
    main()