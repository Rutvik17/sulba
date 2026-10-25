A shop's customer list has an account per line: a name, then one or more email addresses. One person may have made several accounts, and any two accounts that share an address are the same person's, even through other accounts. Different people can share a name, but never an address. Write `merged`:

```
merged(accounts) -> a list with one account for each person: their name, then every address
    from all their accounts, once each, sorted
```

```python
[
    ["Ada", "ada@work.com", "ada@home.com"],
    ["Ada", "ada@old.com"],
    ["Ada", "ada@home.com", "ada@phone.com"],
    ["Bo", "bo@home.com"],
]
```

merges into these, in any order:

```python
[
    ["Ada", "ada@home.com", "ada@phone.com", "ada@work.com"],
    ["Ada", "ada@old.com"],
    ["Bo", "bo@home.com"],
]
```

The tests' longest list has {% $fig.accounts %} accounts, each sharing an address with the next.
