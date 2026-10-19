Three of the problems came from trusting the form's schema to say more than it does. `format` is a note for the application, so the code has to parse the date, and a date that won't parse is an email for a person. A `pattern` without `^` and `$` asks only that the text holds a match somewhere. And an object takes any key its schema doesn't name unless `additionalProperties` is `false`, so a reply held to that schema can still carry them.

The fourth was in a rule no schema holds: the day the shop is closed. Python's `weekday()` counts Monday as `0` and `isoweekday()` counts it as `1`, and mixing them up made a check that was never true, which no test of an open day could find.

Each check scripted a reply a real email can get. With the fixes, a reply the form refuses goes back to the model with its error, an entry the shop can't take goes to a person, and the calendar only gets entries it can use.
