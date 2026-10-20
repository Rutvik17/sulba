The test set's {% $fig.test %} questions come from {% $fig.pages %} pages. At {% $fig.confidence %}:

| Score | Share | Margin, each question alone | Margin, each page's questions together | Design effect |
| --- | --- | --- | --- | --- |
| Passes every check | {% $fig.all_rate %} | ±{% $fig.all_margin %} | ±{% $fig.all_clustered %} | {% $fig.all_effect %} |
| Cites a passage that holds the answer | {% $fig.answer_rate %} | ±{% $fig.answer_margin %} | ±{% $fig.answer_clustered %} | {% $fig.answer_effect %} |

The questions about one page are answered from the same passages, so they pass and fail together: a page the search serves badly takes all its questions down at once. Counted together, the share of replies that pass every check lies between {% $fig.all_low %} and {% $fig.all_high %}. The design effect, the clustered variance over the independent one, says how many questions the set is worth: {% $fig.test %} questions on these pages tell as much as {% $fig.all_worth %} independent ones about every check, and {% $fig.answer_worth %} about citing the answer.

A margin that treats each question alone says the test set knows more than it does. A change the help desk makes would then look real when the test set can't tell it from the questions it happened to draw.
