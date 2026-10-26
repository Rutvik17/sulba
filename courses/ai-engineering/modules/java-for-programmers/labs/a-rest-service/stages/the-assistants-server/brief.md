While you wrote the replies, the IT team asked an assistant to put the desk's server together. The assistant wrote `Server.java`: `Server.start` makes one `HttpServer` with your API, your replies at `/messages` and a health check at `/health`, which the office's load balancer asks every few seconds, and writes a line to the log for each request, through a `Filter`. Its four tests all pass.

Review it as if the desk were about to take calls through it: fix every problem you can find, and keep what it does right. Four hidden checks test it the way the desk will be used. A run shows how many pass, and you see which ones when you finish the review.

What the server must do:

- answer every caller while others are being answered, however slowly any one of them sends;
- give every handler the request's body, whole;
- answer every request to `/health`, whatever its method and path;
- answer every address it doesn't have with problem details.
