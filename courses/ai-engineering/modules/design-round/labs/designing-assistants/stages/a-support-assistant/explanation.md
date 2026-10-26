## What it must do

The assistant answers what the help pages answer and passes the rest to staff. Of the {% $fig.questions %} questions a day, staff think the pages answer about {% $fig.answerable %}: at most {% $fig.answered %} for the assistant, and at least {% $fig.to_staff %} for staff. Questions about an order, a refund or a complaint go to staff whatever the pages say, since only staff can act on them.

## A question's path

1. The question arrives with the chat so far. A quick check sends some to staff at once: an order number, a refund, a complaint.
2. Retrieval finds the question's best passages. The help pages are split by heading, searched by their words and by an embedding of their meaning, the two rankings merged and the best few kept.
3. The model gets its instructions, the passages, each with its page and heading, and the question. It answers from the passages alone and names the page each fact came from.
4. Code checks the answer before it's shown. An answer that cites no passage, or whose best passage scored below the threshold, goes to staff instead, with the chat.
5. The answer streams to the customer with a link to each page it cites, beside a button that passes the chat to staff.

## What it keeps

The index of passages, each with its page, its heading and the page's version. The chats, for staff and for the test set, for as long as the shop keeps chats now. And for each answer, the passages it was given, so a wrong answer can be traced to a page, to the retrieval or to the model.

## Ready to launch

A test set of {% $fig.test_questions %} past questions, drawn from a whole year so that seasonal questions are in it, each with the answer staff gave or a note that it's for staff. Each run grades three things: answers that are right, answers that are wrong, and questions passed to staff. The shop sets a bar for each before launch: the most wrong answers it accepts, and the most handoffs that still save staff time. Every change to the indexing, the prompt or the model runs the set again before it ships. After launch, a sample of real chats each week is graded the same way.

## Safety

The customer's message and the pages are text for the model to read, never instructions it must follow. The assistant has no tool that changes an order or moves money, so the worst a message like "confirm my refund" can do is change what the assistant says. The answer's check stops one that cites nothing.

## Load and cost

The busiest hour carries {% $fig.peak_hour %} questions, {% $fig.peak_rate %} a second. A day is {% $fig.day_in %} tokens in and {% $fig.day_out %} out: {% $fig.cost_in %} for the tokens in and {% $fig.cost_out %} for the tokens out, {% $fig.day_cost %} a day, about {% $fig.month_cost %} over {% $fig.month_days %} days, or {% $fig.per_question %} a question. Most of the cost is the tokens in, so the number and length of the passages sent is the first thing to tune.

## The follow-up questions

- **A page changes:** indexing on publish puts the new policy in answers within minutes. A test question on the new policy, added with the change, shows it.
- **"Confirm my refund":** nothing the assistant can do confirms a refund. The message is about a refund, so it goes to staff.
- **Too many handoffs:** count the test set's handoffs by their reason: no passage found, a low score, or a topic for staff. If retrieval misses passages that exist, improve retrieval first. If the threshold is too strict, lower it only as far as the wrong answers stay under their bar.
