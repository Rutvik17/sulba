The current release's first reply to each question, graded with the passages it was shown, at the threshold of {% $fig.chosen %} that BEGIN's development set chose, at {% $fig.confidence %}:

| Line | Flagged | Margin | Replies |
| --- | --- | --- | --- |
| `all` | {% $fig.all_flagged %} | ±{% $fig.all_margin %} | {% $fig.all_replies %} |
| `dmv` | {% $fig.dmv_flagged %} | ±{% $fig.dmv_margin %} | {% $fig.dmv_replies %} |
| `ssa` | {% $fig.ssa_flagged %} | ±{% $fig.ssa_margin %} | {% $fig.ssa_replies %} |
| `studentaid` | {% $fig.studentaid_flagged %} | ±{% $fig.studentaid_margin %} | {% $fig.studentaid_replies %} |
| `va` | {% $fig.va_flagged %} | ±{% $fig.va_margin %} | {% $fig.va_replies %} |

The grader flags most of the release's replies, and {% $fig.to_read %} go on the list to read. The release's risks start at {% $fig.lowest %}, with a median of {% $fig.median %}, where people's replies with their own passages have a median of {% $fig.own_median %}. The grader also flags {% $fig.own_flagged %} of people's replies with their own passages, so a share this high doesn't say how many of the release's replies are wrong. The list, highest risk first, is where people start reading, and releases are better compared on the grader's scores, question by question, than on the share it flags.
