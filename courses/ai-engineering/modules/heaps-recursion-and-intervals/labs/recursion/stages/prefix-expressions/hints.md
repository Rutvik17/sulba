Split the text into its parts first: parentheses, operators and numbers. Reading one expression then means reading a number, or an operator and some expressions. What reads those?

---

`expression.replace("(", " ( ").replace(")", " ) ").split()` gives the parts. A function that reads one expression from a place in the parts reads a number, or an operator and then expressions up to the `)`, calling itself for each.
