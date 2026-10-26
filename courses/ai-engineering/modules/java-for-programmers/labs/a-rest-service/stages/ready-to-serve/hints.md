`Integer.parseInt` throws `NumberFormatException` for a value that isn't a whole number, such as `1.5` or an empty string. Collect each variable that's wrong in a list, and throw once you've checked them all.

---

`HttpServer.stop(seconds)` stops taking requests, then waits up to `seconds` for the exchanges in flight before it closes their connections.

---

`server.getExecutor()` gives the executor your `Server.start` set. `shutdownNow()` interrupts the tasks still running, and `awaitTermination` waits for them to end.
