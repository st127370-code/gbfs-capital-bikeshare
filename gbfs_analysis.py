"""
Dataset 3 analysis: when do Capital Bikeshare stations actually run empty?

Reads the week of snapshots saved by gbfs_poll.py and produces:
  - fig_gbfs_by_hour.png : % of stations that are empty / full, by hour of day,
                           weekdays vs weekends, with the commute peaks shaded
  - gbfs_summary.csv     : the same numbers as a table
  - a short summary printed on screen, ready to quote in the report

Empty station = no bike available, so a rider who arrives finds nothing (a real stockout).
Full station  = no free dock, so a rider cannot return a bike (the "too many bikes" side).
Only stations that are installed and renting are counted.
"""
import pandas as pd
import matplotlib.pyplot as plt

STATUS_FILE = "gbfs_status.csv"
LOCAL_TZ = "America/New_York"          # Washington, D.C. local time
PEAK_HOURS = [7, 8, 17, 18]            # same commute peaks as H3 in the report (07-09 and 17-19)

import glob, os
files = sorted(glob.glob("data/status_*.csv"))     # daily files saved by GitHub Actions
df = pd.concat([pd.read_csv(f) for f in files]) if files else pd.read_csv(STATUS_FILE)
df["time"] = pd.to_datetime(df["poll_time_utc"], utc=True).dt.tz_convert(LOCAL_TZ)
df = df[(df["is_installed"] == 1) & (df["is_renting"] == 1)].copy()

df["hour"] = df["time"].dt.hour
df["day_type"] = df["time"].dt.dayofweek.map(lambda d: "Weekend" if d >= 5 else "Weekday")
df["empty"] = (df["num_bikes_available"] == 0).astype(int)
df["full"] = (df["num_docks_available"] == 0).astype(int)

print("Snapshots:", df["poll_time_utc"].nunique(), "| stations:", df["station_id"].nunique(),
      "| from", df["time"].min().strftime("%Y-%m-%d %H:%M"), "to", df["time"].max().strftime("%Y-%m-%d %H:%M"))

# share of stations empty / full, averaged over all snapshots in each hour (in %)
by_hour = df.groupby(["day_type", "hour"])[["empty", "full"]].mean().mul(100).round(1).reset_index()
by_hour.to_csv("gbfs_summary.csv", index=False)

# ---------- figure ----------
fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), sharey=True)
for ax, column, title in [(axes[0], "empty", "Stations with no bike (stockout)"),
                          (axes[1], "full", "Stations with no free dock")]:
    for day_type, colour in [("Weekday", "#168FB8"), ("Weekend", "#A86A12")]:
        part = by_hour[by_hour["day_type"] == day_type]
        ax.plot(part["hour"], part[column], marker="o", color=colour, label=day_type)
    for start in (7, 17):                                   # shade the commute peaks
        ax.axvspan(start, start + 2, color="#E8ECF5", zorder=0)
    ax.set_title(title); ax.set_xlabel("Hour of day (local time)")
    ax.set_xticks(range(0, 24, 2)); ax.grid(alpha=.3)
axes[0].set_ylabel("% of stations"); axes[0].legend()
fig.suptitle("Capital Bikeshare, one week of live station data (shaded: commute peaks)")
plt.tight_layout(); plt.savefig("fig_gbfs_by_hour.png", dpi=200)

# ---------- numbers for the report ----------
weekday = df[df["day_type"] == "Weekday"]
peak = weekday[weekday["hour"].isin(PEAK_HOURS)]
off_peak = weekday[~weekday["hour"].isin(PEAK_HOURS)]
busiest = by_hour[by_hour["day_type"] == "Weekday"].sort_values("empty", ascending=False).iloc[0]

print(f"Weekday commute peaks: {peak['empty'].mean() * 100:.1f}% of stations empty "
      f"(other weekday hours: {off_peak['empty'].mean() * 100:.1f}%)")
print(f"Weekday hour with most empty stations: {int(busiest['hour']):02d}:00 "
      f"({busiest['empty']:.1f}% of stations empty)")
print("Saved fig_gbfs_by_hour.png and gbfs_summary.csv")
