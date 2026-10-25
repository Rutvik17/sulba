Which courses can be taken first? Once they're taken, which courses become possible?

---

Count, for each course, the prerequisites it's still waiting on. Start with the courses waiting on none; each time you take one, lower the counts of the courses that need it, and any that reach 0 are ready. If you run out of ready courses before taking them all, some courses need each other.
