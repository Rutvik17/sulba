The desk's Java service answers every error as a problem details object, as RFC 9457 defines it and as the Python desk did, with the media type `application/problem+json`. In `Problems.java`, the starter gives you the records: `Problem(type, title, status, detail, errors)`, which Jackson writes without a detail or errors that's `null`, and `Invalid(detail, pointer)`, one value in a request that doesn't fit.

- `of(status, detail)` gives a problem of type `about:blank`, titled with the status's phrase, with the detail, which may be `null`. The desk answers with 400, 404, 405, 409, 413, 415, 422, 429, 500 and 503, each titled as RFC 9110 names it, and 429 as RFC 6585 does. Any other status is an `IllegalArgumentException`.
- `pointer(path)` gives where a value is in a request's JSON, from the keys and indexes that lead to it, as a JSON Pointer in a URI fragment: `#`, then `/` and each part. Inside a part, `~` is written `~0` and `/` is written `~1`, as RFC 6901 says, and every character a URI fragment can't hold is percent-encoded from its UTF-8 bytes. The whole document is `#`.
- `json(problem)` writes the problem as JSON.

`of(error)` gives the problem for an error. It looks at the error, then its cause, and its cause's cause, and answers for the first that one of these rows names:

| The error | Status | `detail` | `errors` |
| --- | --- | --- | --- |
| `Desk.Refused` | 409 | its message | |
| `InvalidDefinitionException`, Jackson's error for a type it can't make | 500 | | |
| Any other `DatabindException`: the request's JSON doesn't fit its record | 422 | `The request's content doesn't fit.` | one `Invalid`, at the error's path |
| `StreamReadException`: the body isn't JSON | 400 | `The request's body isn't JSON.` | |

With none of them, it's 500, with no detail. An `Invalid`'s detail is the record's own message when its constructor refused the value (a `ValueInstantiationException`), `There's no such field.` for a field the record doesn't have (an `UnrecognizedPropertyException`), and `The value doesn't fit this field.` for any other. Its pointer comes from the error's `getPath()`: each reference's property name, or its index in an array.

```java
public static Problem of(int status, String detail)
public static Problem of(Throwable error)
public static String pointer(List<?> path)
public static String json(Problem problem)
```

The tests read requests as the desk's API does, refusing a field the record doesn't have. They show you which of their cases pass, but not what they gave or expected. Checks then test what the answers need before the desk ships.
