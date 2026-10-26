`np.array(response.json()["data"][0]["embedding"], dtype=np.float32)` gives the vector in the form psycopg sends to Postgres as a `vector`. A list goes as an array of floats, which `<=>` doesn't take.

---

`client.post(..., timeout=5)` gives the request a timeout of its own, whatever the client's.

---

Work out the threshold once, with your `threshold` on the office's validation questions, and keep the number it gives in `office.py`.
