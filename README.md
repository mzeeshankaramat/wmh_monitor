# WMH Service Desk Occupancy Monitor

Records the live occupancy of the War Memorial Hall (WMH) Service Desk from the Virginia Tech Rec Sports occupancy page, and saves each reading to a CSV for analysis.

Source page: https://connect.recsports.vt.edu/facilityoccupancy

## Files

| File | What it is |
|---|---|
| `wmh_monitor.py` | Script that opens the page in a headless browser, reads the occupancy, and appends one row to the CSV. |
| `wmh_occupancy.csv` | The collected data. One row per reading. |
| `wmh_occupancy.backup.csv` | Copy of the CSV taken before rows were removed as closed-time or zero readings. |
| `logs/wmh_monitor.log` | Output from each scheduled run (one line per reading). |
| `logs/wmh_monitor.err.log` | Errors from scheduled runs. |
| `hourly_average_occupancy.png` | Chart: average occupancy % by hour, all days. |
| `hourly_occupancy_weekdays.png` | Chart: average occupancy % by hour, weekdays. |
| `hourly_occupancy_weekends.png` | Chart: average occupancy % by hour, weekends. |

## CSV format

| Column | Meaning |
|---|---|
| `timestamp` | Local time (America/New_York), `YYYY-MM-DD HH:MM` |
| `occupancy` | Number of people in the facility |
| `occupancy_percent` | `occupancy / max_capacity * 100`, rounded to 1 decimal |
| `remaining` | Spaces left (`max_capacity - occupancy`) |
| `max_capacity` | Capacity reported by the site (1200) |

## Setup

The script runs in the conda environment `wmh-monitor`, which already has Playwright and Chromium installed.

If you ever need to recreate it:

```bash
conda create -n wmh-monitor python=3.11
conda activate wmh-monitor
pip install playwright
python -m playwright install chromium
```

## Run manually

From this folder:

```bash
/opt/anaconda3/envs/wmh-monitor/bin/python wmh_monitor.py
```

Each run prints one line like `2026-10-05 16:00 | 671 | 56.0% | 529 remaining` and appends a row to `wmh_occupancy.csv`. If the page fails to load, the script retries 3 times and then records a `FETCH FAILED` line without writing to the CSV.

## Automatic schedule (launchd)

The job runs every 30 minutes from **6:00 AM to 10:30 PM** (35 runs a day) and is idle overnight. It is defined in:

`~/Library/LaunchAgents/com.zeeshan.wmh-monitor.plist`

Its label is `com.zeeshan.wmh-monitor`.

Times are set with `StartCalendarInterval`, one entry per half hour from 06:00 through 22:30. To change the hours, edit the plist and reload it (see below).

### Check status

```bash
launchctl list | grep wmh-monitor
```

A `-` in the first column means the job is loaded and waiting for its next run. A number means it is running or ran with that exit code.

### Stop the routine

```bash
launchctl unload ~/Library/LaunchAgents/com.zeeshan.wmh-monitor.plist
```

### Start the routine again

```bash
launchctl load ~/Library/LaunchAgents/com.zeeshan.wmh-monitor.plist
```

### After editing the schedule

```bash
plutil -lint ~/Library/LaunchAgents/com.zeeshan.wmh-monitor.plist
launchctl unload ~/Library/LaunchAgents/com.zeeshan.wmh-monitor.plist
launchctl load ~/Library/LaunchAgents/com.zeeshan.wmh-monitor.plist
```

### Notes on the schedule

- The job only runs while you are logged in and the Mac is awake. If the Mac is asleep at a scheduled time, launchd runs it shortly after wake.
- The job is unaffected if you close the terminal.

## Troubleshooting

- **No new rows:** check `logs/wmh_monitor.err.log` and run the script manually.
- **Empty or changed values:** the page sometimes returns a stale value for several hours (for example, a run of identical readings). Check the CSV before trusting a long flat stretch.
- **Playwright or browser errors after an update:** reinstall the browser with `python -m playwright install chromium` inside the `wmh-monitor` environment.

## Data notes

- Weekend hours close at 10 PM and weekdays at 11 PM, so 10 PM and later readings on weekends are removed from analysis.
- Rows with 0 occupancy (the facility was closed) and rows after closing time on weekends were removed from `wmh_occupancy.csv`. The original data is kept in `wmh_occupancy.backup.csv`.
- Analysis charts use only the hours with at least 5 readings. In the averages, `n` is the number of readings that went into that hour's bar.
