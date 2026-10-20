Of the {% $fig.questions %} questions, {% $fig.repeated %} have the same words as an earlier one, and {% $fig.repeated_elsewhere %} of those are about another page. Each counted twice would weigh twice, and one on each side would score the test set on a question the development set tuned for. That leaves {% $fig.unique %}. With a share of {% $fig.share %} and `default_rng(0)`:

| Service | Development | Test |
| --- | --- | --- |
| `dmv` | {% $fig.dev_dmv %} | {% $fig.test_dmv %} |
| `ssa` | {% $fig.dev_ssa %} | {% $fig.test_ssa %} |
| `studentaid` | {% $fig.dev_studentaid %} | {% $fig.test_studentaid %} |
| `va` | {% $fig.dev_va %} | {% $fig.test_va %} |

The test set holds {% $fig.test_questions %} questions about {% $fig.test_pages %} pages, and the development set {% $fig.dev_questions %} about {% $fig.dev_pages %}. Each service keeps its share on both sides, so a change that helps one service and hurts another is measured on each as the help desk meets it.

Pages move whole, so a side can go past its share by most of a page: {% $fig.largest_pages %} pages hold {% $fig.largest_page %} questions each. The same share drawn question by question would put {% $fig.mixed_pages %} pages on both sides, and {% $fig.mixed_questions %} of the test questions, {% $fig.mixed_share %}, would be about a page the development set has questions on.
