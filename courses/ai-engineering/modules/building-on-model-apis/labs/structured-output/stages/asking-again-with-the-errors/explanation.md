A model that gets the same conversation again tends to write the same reply again, so asking again only helps when the conversation changes. Sending the reply back as the model's own, with what's wrong with it as the user's, gives the model both: what it wrote and what to fix. Each line names the path and the rule, the same detail a person fixing the booking would want.

Each attempt is a request, paid for in time and tokens, and every request after the first carries the replies and problems before it. So the attempts are few, and when the last fails, `NoMatch` hands the email to a person with what went wrong.

A reply cut off at its token limit is never read. Its text stops where the limit fell, and whatever the model meant to write after it, the booking would be missing. The model is told what happened instead.

With `strict`, OpenAI's API takes only schemas whose objects list every property in `required` and set `"additionalProperties": false`, since it generates only the keys a schema names. A field that may be empty is still required, with `null` among its types, as the booking's `phone` is.
