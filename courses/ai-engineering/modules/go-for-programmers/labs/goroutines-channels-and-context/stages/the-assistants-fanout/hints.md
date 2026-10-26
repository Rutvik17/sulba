Follow each goroutine to its end: what happens to its send after `Fanout` has returned?

---

Look at which context each call to an upstream gets, and at what every wait in the loop waits for.
