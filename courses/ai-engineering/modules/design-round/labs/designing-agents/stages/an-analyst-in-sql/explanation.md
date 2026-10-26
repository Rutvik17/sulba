## What it must do

Answer managers' questions with numbers that are right and that mean what the company means by them, without any query that harms the warehouse or shows what managers may not see. The team's analysts answer about {% $fig.questions %} questions a week at {% $fig.analyst_minutes %} minutes each: {% $fig.analyst_hours %} hours a week, which is what the assistant can give back.

## Finding the tables

{% $fig.tables %} tables are too many to send with every question. Each table has a description, its columns with theirs, and sample questions it answers, written once by the data team and indexed for search. A question's best few tables, with their columns, go to the model, and it can ask for more through a tool.

## Agreed definitions

Sales, returns and active customers have definitions the company agreed: which tables, which filters, which dates. They live in the warehouse as views, and the model is told to build on them, not on raw tables. So two managers who ask about last month's sales get the same number, from the same view.

## Running a query

- The query runs as a read-only role that can read the views and tables managers may see, and nothing else.
- Before it runs, the planner's estimate of its cost is checked against a limit. A query over the limit is refused with the reason, and the model can narrow it.
- It runs with a time limit and a row limit.

## Checking the answer

Code checks that the query ran, that it returned rows, and that each number in the answer appears in the result. A failed or empty result is retried once with the error, then passed to an analyst with the question and the attempts.

## Showing its working

Each answer shows the SQL it ran, the views and tables it used, and the definitions behind them, so a manager can see what was counted and an analyst can check it in a minute.

## Measuring

A test set of past questions with the analysts' answers is scored on whether the numbers match, run on every change to the descriptions, the views, the prompt or the model.

## The follow-up questions

- **A query over {% $fig.sales_rows %} rows:** the planner's estimate is over the limit, so the query is refused before it runs. The model narrows it by date, or uses a monthly summary view.
- **Two numbers for last month's sales:** both should come from the sales view. If they differ, one answer didn't use it, which its shown SQL makes plain, and the test set gains that question.
- **Email addresses:** the role can't read the columns with personal data, so the query fails whatever it asks, and the assistant says the data isn't available to it.
