# Collections, streams and the JVM

The lab's stages, run on your machine. Install [uv](https://docs.astral.sh/uv/), then in this folder run:

```sh
uv run sulba.py
```

It runs the tests of the stage you're on. When the stage is done, it gives you a link that marks it done on the lab's page. Start the next stage with `uv run sulba.py next`, and finish a Catch stage's review with `uv run sulba.py finish`.

The stages are Java, in this one folder, with no package, so an IDE opens it as it is. Every class can use Jackson for JSON, and the tests use JUnit. The first run downloads a JDK for your system from github.com, and JUnit and Jackson from repo1.maven.org, into `sulba` in your cache folder.
