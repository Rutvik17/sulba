Before the dispatcher relies on the pipeline, it needs tests of its own, which run whenever its code changes. In `test_pipeline.py`, write tests of `weather(spark)`, `daily(spark, flagged, weather)` and `against_dry_days(daily)`. They run with pytest, and each test can ask for the `spark` fixture, as the lab's own tests do. Run them with `uv run pytest test_pipeline.py`.

Your tests must pass on your pipeline. Then the checks plant one problem at a time in it, each in one of those three functions, and run your tests again: at least one of them must fail on each.

A test that reads August's files tests only what August happens to hold, and the trip files take seconds to read. A test can build its own input instead:

- `spark.createDataFrame(rows, schema)` makes a table of flagged trips, weather or daily rows from a list of tuples and a schema such as `"pickup_zone int, pickup_at timestamp_ntz, clean boolean"`;
- for `weather`, a test can write a file in the service's layout to `tmp_path` and point `weather.py` at it with `monkeypatch.setattr(weather_file, "WEATHER", str(path))`, where `weather_file` is the module, `import weather as weather_file`.
