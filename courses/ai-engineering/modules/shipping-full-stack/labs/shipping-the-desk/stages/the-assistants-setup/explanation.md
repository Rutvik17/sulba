Each problem passed the assistant's tests because every test ran the desk the way a laptop does: requests without a query, a model that answered at once, checks that never hung, and a server reached from the same machine.

What a log holds lasts and travels: a host keeps it, people search it, and it goes to whoever helps with a problem. OWASP's Logging Cheat Sheet lists "Access tokens" and "Session identification values" among what "should usually not be recorded directly in the logs". A query is where an address puts what a request carries, so the request line leaves it out.

A readiness check runs every few seconds for as long as the desk runs, so it has to be cheap. llama.cpp's server says at `/health` whether the model has loaded, which costs it nothing, where a reply, even of one token, runs the model.

A limit on each check is what lets `/ready` answer at all when something hangs. Libraries' timeouts are made for their own work: a pool's for the wait for a connection, and a client's for a reply that may stream for minutes.

`127.0.0.1` is the loopback address, which only the machine itself reaches. Render: "Every Render web service must bind to a port on host 0.0.0.0 to serve HTTP requests. Render forwards inbound requests to your web service at this port (it is not directly reachable via the public internet)." The proxy in front keeps the desk off the internet, so listening on every address of the container is safe.
