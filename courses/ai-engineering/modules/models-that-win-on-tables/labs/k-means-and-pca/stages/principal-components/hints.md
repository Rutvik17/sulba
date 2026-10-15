`np.linalg.eigh` gives the eigenvalues from the smallest up and the eigenvectors as the columns of its second array, in the same order. `[::-1]` turns an array around, and `vectors[:, ::-1].T` puts the eigenvectors in rows, the largest first.

---

For each row, `np.abs(row).argmax()` finds the entry farthest from 0, and `np.sign` of that entry is the factor that turns the row the right way round.

---

`project` is one matrix product: each row of `Z` with each row of `directions`.
