`http.NewRequestWithContext(ctx, http.MethodPost, url, bytes.NewReader(body))` makes the request, and `client.Do` sends it. Once `Do` gives no error, `defer response.Body.Close()`.

---

`io.LimitReader(response.Body, 1<<20)` stops reading at a megabyte, so the decoder sees a reply cut short and gives an error.

---

`strconv.Atoi(response.Header.Get("Retry-After"))` gives the seconds, or an error for a header that's missing or not a number.
