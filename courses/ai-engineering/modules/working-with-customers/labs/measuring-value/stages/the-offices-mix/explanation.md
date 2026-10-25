Weighted by the test set's own tasks, the desk does {% $fig.tests %}, from {% $fig.tests_low %} to {% $fig.tests_high %}. Weighted by the office's contacts, it does {% $fig.office %}, from {% $fig.office_low %} to {% $fig.office_high %}. The desk is the same; the office's contacts are {% $fig.questions %} questions, the kind it does least often. A test set's headline share holds only for contacts in the test set's proportions, and every customer's mix is its own.

The variance of a sum of separate estimates is the sum of their variances, and a weight multiplies a standard error, so each kind adds `$w_k^2 s_k^2$`. The questions carry the most weight and the widest error, and add {% $fig.question_part %} of the variance: more question tasks would narrow the office's interval more than anything else.

The interval stops at 0 and 1 because a share can't go past them.
