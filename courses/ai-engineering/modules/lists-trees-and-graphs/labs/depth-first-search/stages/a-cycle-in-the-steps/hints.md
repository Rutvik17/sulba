Follow the needs from a step, depth first. When does the walk prove there's a cycle?

---

Keep the steps on the current path, and the steps already finished. Reaching a step on the path closes a cycle: the path from it to here. Reaching a finished step adds nothing.
