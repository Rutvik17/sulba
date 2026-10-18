`np.linalg.norm(np.ravel(tensor), ord=norm_type)` is one array's norm, in any norm type. The total is the same norm of the array of those norms.

---

Scale in place with `grad *= scale`, so that the arrays the caller holds are the ones that change.
