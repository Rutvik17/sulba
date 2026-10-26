`strings.CutPrefix(r.Header.Get("Authorization"), "Bearer ")` gives the key, and whether the header started with `Bearer `.

---

Read the body through `http.MaxBytesReader(w, r.Body, s.MaxBody)`. A body over the limit makes `DecodeRequest` give an error with a `*http.MaxBytesError` inside, which `errors.AsType` finds.

---

Set every header before you write the body: `json.NewEncoder(w).Encode(...)` sends the headers with its first write.
