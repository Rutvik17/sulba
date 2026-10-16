The assistant's tests compared values written in the tests themselves, where `is` happened to hold, and passed no boolean, no falsy value and no record they looked at after the call.

---

Each problem was JavaScript read as Python: `===` taken for `is`, `includes` for `in`, a test of truth for a test of whether a field was sent, and a new name for a copy. In a port, each of these is worth checking against what the original does.
