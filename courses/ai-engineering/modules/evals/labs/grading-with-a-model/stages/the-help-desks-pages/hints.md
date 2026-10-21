`(index + len(questions) // 2) % len(questions)` is the place half the list on, going round.

---

`questions[start:] + questions[:start]` goes round the list from `start`, so `next` over it finds the first question from another service.

---

`verdicts[labels == 1]` gives the verdicts on the replies labelled 1.
