The next item is the smallest of the streams' next items. Which item does each stream need to have read so far?

---

Keep each stream's next item on a heap with the stream's place, so two equal items never compare the streams themselves. After giving the smallest, read its stream's next item, or drop the stream when it has none.
