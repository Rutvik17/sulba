## What it must do

A summary of every call within an hour, and a weekly view that counts problems the same way every week. The summaries are read by managers, so they must be right more than they must be fast, and they must not carry what the company shouldn't keep, such as card numbers.

## The summary's shape

Each summary is structured output in a schema, as in Structured output: a list of problems, each with a category from the company's list, a sentence on what was done, and solved, not solved or passed on. A call with two problems has two entries. Code validates each summary against the schema, and one that fails is retried, then sent to a person.

## The pipeline

1. The phone system puts each ended call's transcript on a queue.
2. A worker removes card numbers and other personal data from the transcript.
3. The worker asks the model for the summary, validates it and stores it with the call's id, the category list's version and the model's.
4. Workers retry a failed call with a growing wait, and a call that still fails goes to a person.

A queue fits the hour: it smooths the day's peaks, rides out short failures, and lets the workers run as fast as the provider allows.

## Personal data

Card numbers are found with a pattern for the digits, checked with the check digit every card number carries, and replaced before the model sees the transcript. Names, addresses and account numbers go the same way. The stored summary is checked for them again, so a summary never holds what the transcript lost.

## The weekly view

The weekly view counts the structured fields: problems by category, and how many were solved. A call with two problems counts once in each category. The category list has a version, so a week counted with a new list says so, and its counts aren't set beside the old ones as if they were the same.

## Measuring

Each week a team lead grades {% $fig.sample %} summaries against their calls: whether each problem is there, whether its category is the one the lead would choose, and whether solved is right. Agreement on the categories is the number to watch, since the weekly view rests on it.

## An outage

While the provider is down, calls wait on the queue. Two hours make a backlog of {% $fig.backlog %} calls. To clear it in an hour while new calls keep coming, the workers need {% $fig.clear_rate %} calls a second, so the design sets the workers and the provider's rate limit for that. Summaries past their hour are marked late, and the weekly view isn't affected.

## Load and cost

{% $fig.calls %} calls over {% $fig.hours %} hours is {% $fig.per_hour %} an hour, {% $fig.rate %} a second. Each is {% $fig.call_in %} tokens in, {% $fig.day_in %} a day, and {% $fig.summary %} out, {% $fig.day_out %} a day: {% $fig.day_cost %} a day.

## The follow-up questions

- **Two problems:** two entries, one solved and one not, and the weekly view counts each problem in its own category.
- **Card numbers:** removed from the transcript before the model, and the summary checked again before it's stored.
- **A two-hour outage:** the queue holds {% $fig.backlog %} calls. They're cleared at {% $fig.clear_rate %} calls a second, and the late ones are marked.
