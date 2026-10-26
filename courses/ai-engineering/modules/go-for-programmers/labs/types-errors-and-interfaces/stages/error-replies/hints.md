`errors.Is` and `errors.AsType` each find one error. To see every `*StatusError`, follow the tree yourself: a type switch on `interface{ Unwrap() error }` and `interface{ Unwrap() []error }` gives each error's children.

---

`math.Ceil(wait.Seconds())` rounds a wait up to whole seconds, and `strconv.Itoa` writes it.

---

Set the headers before `w.WriteHeader(status)`, then write the body with `json.NewEncoder(w).Encode(...)`.
