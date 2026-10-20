`range(0, len(texts), batch)` gives the first place of each batch, and `texts[start : start + batch]` the batch itself.

---

`sorted(response.json()["data"], key=lambda item: item["index"])` puts a reply's vectors in the order of the texts it was sent.

---

`np.array(rows, dtype=np.float32)` makes the array from a list of rows, and `np.zeros((0, 0), dtype=np.float32)` the empty one.
