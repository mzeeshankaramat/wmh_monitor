# WMH Occupancy Monitor - notes for Claude Code

Read README.md first for the full user guide. This file is the working context for a Claude session.

## What this is
Scrapes the WMH Service Desk occupancy from https://connect.recsports.vt.edu/facilityoccupancy every 30 minutes (launchd, 06:00 to 22:30) and appends one row to wmh_occupancy.csv. The CSV is used for analysis and charts.

## Files
- wmh_monitor.py - the scraper (Playwright, headless Chromium). Writes one CSV row per successful run.
- wmh_occupancy.csv - live data. Written by the scheduled job, so re-read it before editing.
- wmh_occupancy.backup.csv - raw copy taken before cleaning. Do not edit.
- analysis/plot_hourly_occupancy.py - makes hourly_occupancy_weekdays.png and hourly_occupancy_weekends.png.
- launchd/com.zeeshan.wmh-monitor.plist - copy of the LaunchAgent (installed at ~/Library/LaunchAgents/).
- logs/ - scheduled run output (wmh_monitor.log, wmh_monitor.err.log).

## Environment
- Scraper: needs Python with playwright and Chromium installed. The author used a conda env named wmh-monitor (Python 3.11). Create it per README.md.
- Charts: need matplotlib in any Python (`pip install matplotlib`).
- Everything uses absolute paths to /Users/zeeshankaramat/... in the launchd plist. On another machine, edit ProgramArguments, WorkingDirectory, and the log paths in the plist before loading it.

## Scheduling
- Status: STOPPED on 2026-10-05 (unloaded). Reload with `launchctl load ~/Library/LaunchAgents/com.zeeshan.wmh-monitor.plist` to resume.
- LaunchAgent label: com.zeeshan.wmh-monitor
- Plist: ~/Library/LaunchAgents/com.zeeshan.wmh-monitor.plist. A copy is in launchd/ in this folder; keep the two in sync.
- Uses StartCalendarInterval with 35 entries (06:00 through 22:30 every 30 min). Do not switch to StartInterval; it cannot respect the opening window.
- Commands: `launchctl load|unload <plist>`, status `launchctl list | grep wmh-monitor`.

## Data rules (already applied to wmh_occupancy.csv)
- Facility closes 22:00 on weekends and 23:00 on weekdays.
- Removed rows with occupancy 0 (closed), the 0.0% row, and weekend rows after 22:00.
- Known bad data kept in the file: stuck/repeated readings on some mornings (Sep 26, Sep 27, and Oct 2 15:30 to Oct 3 09:42). Flag these in any analysis rather than silently dropping them.
- The file is rewritten in place by cleanup scripts; use a temp file and os.replace, then chmod 644 (the default temp-file mode is 600).

## Analysis conventions
- Percent = occupancy / max_capacity * 100 (max_capacity is 1200).
- Hourly averages by hour-of-day, split weekday (Mon-Fri) vs weekend (Sat-Sun).
- Drop hours with fewer than 5 readings from charts. Show n under each bar.
- Percent y-axis, value above each bar, single series with no legend.
