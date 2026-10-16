The service checks each day's codes against the registry before the day's records go on to screening. The registry's terms allow a few lookups at a time, and now and then a lookup is slow, or dropped. Write:

```
check_day(codes, registry, limit, seconds) -> each code's check, in order, with no more
    than limit lookups at a time, each given seconds
```

where a code's check is `None` for a known code, or one of these messages:

```
No patient has the code 'S00002'
The registry couldn't be reached for 'S00002'
The registry took too long for 'S00002'
```

A dropped lookup raises `ConnectionError`. Any other error a lookup raises is a bug: it ends the day, and `check_day` raises it. Hidden tests check what `check_day` gives, and three checks test it before it ships.
