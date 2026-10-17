The assistant's tests checked the shape of what `train` returns, so they passed. The service relies on more: a model that learned from every stay, a threshold set by the probabilities rather than by the share, and a recall and precision measured on stays the model never saw. Each problem shows up only there. Together they would have had the service call {% $fig.at_share %} of the {% $fig.stays %} stays, where the planners can call {% $fig.planned %}, and told the planners to expect a recall of {% $fig.told_recall %} at a precision of {% $fig.told_precision %}. New stays get {% $fig.got_recall %} and {% $fig.got_precision %}.

---

Each problem would have reached the planners as a number they believed: a recall too high, a list too long, or a model that never learned from {% $fig.held %} of the stays. None of them failed or warned.
