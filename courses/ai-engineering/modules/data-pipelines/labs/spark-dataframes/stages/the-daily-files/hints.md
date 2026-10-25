`trips.write.parquet(path)` writes a folder of files. Writing straight over the day's folder with `mode("overwrite")` would make the old files go before the new ones are there.

---

Write the day into a new folder outside `folder`, such as one `tempfile.mkdtemp(dir=...)` makes beside it, then move the old folder out of the way and the new one in with `Path.rename`. A folder inside `folder` would be read as part of the table.

---

`trips.isEmpty()` tells a day with no clean trips. `spark.read.parquet(folder)` gives each row a `day` from its folder's name; cast it to a date.
