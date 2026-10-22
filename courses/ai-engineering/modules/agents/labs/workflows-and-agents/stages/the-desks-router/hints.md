`Workflow(client, desk, page).reply(message, found)` follows a route found already, without a request to sort it again.

---

A callback the workflow can place names a service and a day, and the caller has at most one open ticket for that service: count the desk's `tickets` whose `service` is the route's and whose `status` is `open`.

---

Keep the path the first message chose in an attribute, `None` until then, and send every later message to it.
