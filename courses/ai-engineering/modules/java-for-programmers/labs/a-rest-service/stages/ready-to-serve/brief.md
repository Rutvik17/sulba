The desk's server is put together. In `App.java`, make it a service the office can run, with its settings from the environment and a stop that lets callers finish:

- `settings(environment)` gives the service's `Settings` from the environment's variables, such as `System.getenv()`. `DESK_HOST` and `DESK_PORT` are where it listens, `DESK_RUNNING` and `DESK_WAITING` are its gate's running places and places in line, `DESK_SECONDS` is each reply's limit, and `DESK_GRACE` is how many seconds a stop waits for the requests in flight. Each is a whole number but the host. A variable that isn't set takes its default, from `VARIABLES`.
- `start(settings, desk, agent, log)` starts the desk's server, from your `Server.java`, with a gate from the settings, and gives the `App`. `address()` gives the address it listens at, which has the port the system chose when `DESK_PORT` is 0.
- `stop()` stops the service and returns once every request has ended.

What the service must do:

- refuse settings that don't fit, naming each variable that's wrong;
- run its gate with the settings' places, line and limit;
- let a reply that's being written when it stops finish, for up to the grace;
- once the grace is up, end every reply still running before `stop` returns.

How it does so is yours to choose.

```java
public record Settings(String host, int port, int running, int waiting, Duration limit, int grace)
public static Settings settings(Map<String, String> environment)
public static App start(Settings settings, Desk desk, Agent agent, Consumer<String> log) throws IOException
public InetSocketAddress address()
public void stop() throws InterruptedException
```

Three tests run on every attempt. Then four checks run before the code ships.
