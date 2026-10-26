Before you started, the office asked an assistant for the figures its dashboard shows through the day. The assistant wrote `Stats.java`, which uses your `Reports.Asked`: it holds the day's questions, forgets those from before a time, and gives each page's slowest reply, the busiest pages, and each service's questions by the hour. Its five tests all pass.

Review it as if the dashboard were about to show the office its figures: fix every problem you can find, and keep what it does right. Four hidden checks test it the way the dashboard will use it. A run shows how many pass, and you see which ones when you finish the review.

What the code must do:

- forget every question from before the time it's given, wherever it is in the day's list;
- give the slowest reply of a page asked about more than once;
- give every page tied for the most questions, however many questions that is;
- count each hour and service apart, over a day with more than one hour.
