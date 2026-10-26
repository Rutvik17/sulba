A company's {% $fig.teams %} product teams each call hosted models directly, with their own keys. Last month's bill came to {% $fig.month_bill %}, and nobody can say which team spent what. When one provider had an outage, three products went down with it. The platform team wants a gateway that every model call goes through.

Design it. Take these as given:

- the teams make about {% $fig.calls_day %} calls a day, and at most {% $fig.peak_rps %} a second;
- about {% $fig.repeat_share %} of calls repeat a request made in the last day.
