`np.mean(train, axis=0)` and `np.std(train, axis=0)` give one number for each measurement, and NumPy's `std` divides by the number of beans unless told otherwise.

---

Both arrays are scaled by `train`'s two rows of statistics, which broadcast over every bean: `(other - mean) / sd`.
