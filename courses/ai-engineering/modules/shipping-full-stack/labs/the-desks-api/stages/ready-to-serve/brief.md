The desk's routes are written. In `app.py`, put the app together to serve, so that `uv run uvicorn app:create_app --factory` runs it:

- `settings_from(environ)` gives the app's `Settings` from the environment's variables. `DESK_MODEL_URL` is where the model answers, `DESK_RUNNING` and `DESK_WAITING` are how many replies the gate lets run and wait, and `DESK_SECONDS` is each reply's limit. A variable that isn't set takes its default, from `VARIABLES`.
- `create_app(settings=None, data=Path("data"), client=None)` gives the app, with the settings given, or the environment's when none are. As the app starts, it makes one client to the model for every request, unless it's given one, and loads the help pages from `data` with `load_search`. Then it keeps these in `app.state`:
  - `client`, the client;
  - `desk`, the `Desk`, on the caller's `TICKETS` and the advisers' `free_times()`;
  - `conversations`, the conversations;
  - `gate`, the gate, from the settings;
  - `agents`, whose `make` gives each conversation an `Agent` on the one client, with an `Actions` on the one desk.

  As the app stops, it closes the client it made. The app has the conversations' routes and the replies' route, gives its errors as problem details, and answers `GET /health` with `{"status": "ok"}`.

What the app must do:

- refuse settings that don't fit, naming each variable that's wrong;
- make one client to the model, which waits for each read as long as a reply's limit, and close it as the app stops;
- load the help pages once, for every conversation;
- answer its health check at once while it's replying.

How it does so is yours to choose.

```
settings_from(environ) -> Settings
create_app(settings=None, data=Path("data"), client=None) -> FastAPI
GET /health
```

Three tests run on every attempt. Then four checks run before the code ships.
