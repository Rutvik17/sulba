The assistant's tests used values that every range in the spec allowed, so each field passing its own range and each field taking the last range looked the same. None changed a list after a check was made, read a check's name, or sent a value of the wrong kind.

---

Each problem came from when a closure reads what it holds: a `lambda` reads its variables when it's called, so a loop must bind each row's values when the check is made; a check reads a list it was given each time it runs, so it needs a copy; and a refinement must read its value only once the check has passed it. A wrapper needs `functools.wraps`, or it shows its own name in place of the function's.
