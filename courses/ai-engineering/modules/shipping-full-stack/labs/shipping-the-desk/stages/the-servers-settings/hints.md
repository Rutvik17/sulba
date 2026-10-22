`uvicorn.Config` takes `host`, `port`, `proxy_headers`, `forwarded_allow_ips`, `timeout_graceful_shutdown`, `log_config` and `access_log`, among others. `log_config=None` leaves logging as the desk set it.

---

`app.add_middleware(RequestIds)` puts the middleware around the app, and `app.include_router(router)` adds `/ready`.
