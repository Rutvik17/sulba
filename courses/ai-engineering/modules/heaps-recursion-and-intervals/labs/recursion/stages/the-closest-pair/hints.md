Split the points by x into a left half and a right half, and find each half's closest pair. Where else can the closest pair be?

---

With d the closest distance within either half, a closer pair across the split has both its points within d of the line between the halves. Sorted by y, each of those needs comparing only with the next few, stopping once the gap in y alone reaches d.
