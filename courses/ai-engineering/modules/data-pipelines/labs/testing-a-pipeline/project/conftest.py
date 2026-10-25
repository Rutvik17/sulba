"""The spark fixture your tests ask for, as the lab gives it."""

import pytest
from pysail.spark import SparkConnectServer
from pyspark.sql import SparkSession


@pytest.fixture(scope="session")
def spark():
    """A Spark session for the run's tests, through Spark Connect to a Sail server in this
    process. Its time zone is UTC."""
    server = SparkConnectServer(ip="127.0.0.1", port=0)
    server.start()
    _, port = server.listening_address
    session = SparkSession.builder.remote(f"sc://127.0.0.1:{port}").getOrCreate()
    session.conf.set("spark.sql.session.timeZone", "UTC")
    try:
        yield session
    finally:
        session.stop()
        server.stop()
