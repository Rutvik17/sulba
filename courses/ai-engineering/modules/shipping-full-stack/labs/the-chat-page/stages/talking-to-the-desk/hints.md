`fetch`'s `headers` option takes an object, such as `{ Accept: 'application/json' }`. Add `'Content-Type'` to it only when there's a body.

---

`response.headers.get('Content-Type')` can carry a charset after the type, such as `application/json; charset=utf-8`, so test the start of it.

---

A function kept in a field and called as `this.#fetch(...)` gets the desk as its `this`. Keep an arrow function in the field instead, `(input, init) => fetcher(input, init)`, which calls `fetcher` on its own.
