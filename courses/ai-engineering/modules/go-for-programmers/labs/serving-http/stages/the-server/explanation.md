Go 1.22's `ServeMux` reads a method in a pattern, so `"POST /v1/chat/completions"` takes only a POST. The Go blog's post on the change says what happens to a GET: "In accordance with HTTP semantics, a net/http server will reply to such a request with a 405 Method Not Allowed error that lists the available methods in an Allow header." The handler checks no method itself.

The server runs each connection on its own goroutine: `Serve` "accepts incoming HTTP connections on the listener l, creating a new service goroutine for each." Every request for a key asks the same bucket at once, which is why `Bucket` guards its tokens with a mutex.

The checks run cheapest first. A request without a key, or over its key's limit, is refused before its body is read, so an unknown caller costs the gateway a header and nothing more. RFC 9110 sets what a 401 carries: "The server generating a 401 response MUST send a WWW-Authenticate header field", and RFC 6750, which defines `Bearer` tokens, says the scheme in that challenge "MUST be followed by one or more auth-param values", such as its `realm`. RFC 6585 says a 429 "MAY include a Retry-After header indicating how long to wait before making a new request."

`http.MaxBytesReader` is the body's limit. Its docs: it "prevents clients from accidentally or maliciously sending a large request and wasting server resources", and gives "a non-nil error of type *MaxBytesError for a Read beyond the limit". RFC 9110's 413 "indicates that the server is refusing to process a request because the request content is larger than the server is willing or able to process."

`Fallback` gets `r.Context()`. For a server's request, "the context is canceled when the client's connection closes, the request is canceled (with HTTP/2), or when the ServeHTTP method returns", so when a caller hangs up, the gateway stops asking upstreams for a reply no one will read.

The reply's headers go first. `ResponseWriter`'s docs: "Changing the header map after a call to WriteHeader (or Write) has no effect", and the encoder's first write sends them with a 200. Set `X-Upstream` after `Encode` and the caller never sees it.
