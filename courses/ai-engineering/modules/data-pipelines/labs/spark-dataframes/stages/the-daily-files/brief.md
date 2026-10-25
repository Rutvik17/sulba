The dispatcher's dashboards read each day's clean trips from Parquet files, a folder for each day, and the job that writes them runs again whenever a day's records are corrected. On 5 August, {% $fig.fifth %} of the day's {% $fig.fifth_all %} trips are clean. In `store.py`, write `save(flagged, folder, day)` and `load(spark, folder)`.

`save` writes the day's clean trips from your flagged trips, with the trips' own columns and none of the flags, as Parquet in the day's folder, `folder/day=YYYY-MM-DD`, which `day_folder(folder, day)` gives:

- Saving a day again replaces what was saved for it, and leaves every other day's files as they were.
- The old files go only once the new ones are written in full, so a run that fails partway leaves the day as it was.
- A day with no clean trips has no folder, and loses what was saved for it before.

`load` reads every saved day back: the trips' columns, then `day`, a date, from each folder's name.

```
save(flagged, folder, day) -> None
load(spark, folder) -> DataFrame
```
