Here an address is four whole numbers from 0 to 255 joined by dots, such as `192.168.1.10`, and none of the four has a leading zero, so `01` is never one of them. Write `addresses`:

```
addresses(digits) -> every address the digits can be, with three dots put in, in sorted order
```

`addresses("25525511135")` returns `["255.255.11.135", "255.255.111.35"]`, and `addresses("0000")` returns `["0.0.0.0"]`. The tests' longest string has {% $fig.digits %} digits.
