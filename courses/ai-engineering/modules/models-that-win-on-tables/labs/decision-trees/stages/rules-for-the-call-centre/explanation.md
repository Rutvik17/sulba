```python
def rules(tree, columns):
    found = []

    def visit(node, conditions):
        if "column" not in node:
            leaf = {
                "conditions": conditions,
                "calls": node["calls"],
                "yes": node["yes"],
            }
            found.append(leaf)
            return
        column, threshold = columns[node["column"]], node["threshold"]
        left, right = dict(conditions), dict(conditions)
        if isinstance(column, tuple):
            name, category = column
            _, ruled_out = conditions.get(name, ("is not", []))
            left[name] = ("is not", sorted([*ruled_out, category]))
            right[name] = ("is", category)
        else:
            low, high = conditions.get(column, (-np.inf, np.inf))
            left[column] = (low, min(high, threshold))
            right[column] = (max(low, threshold), high)
        visit(node["left"], left)
        visit(node["right"], right)

    visit(tree, {})
    return sorted(found, key=lambda rule: -rule["yes"] / rule["calls"])
```

Each side of a split gets its own copy of the conditions, so the left path's conditions never leak into the right's. `sorted` keeps equal keys in their order, so rules with equal shares stay in the tree's.

The tree grown {% $fig.depth %} deep with at least {% $fig.min_leaf %} calls a leaf gives {% $fig.rules %} rules. The likeliest is `pdays` above {% $fig.top_low %} and at most {% $fig.top_high %}, with `education` `university.degree`: {% $fig.top_yes %} of its {% $fig.top_calls %} training calls said yes. The largest holds {% $fig.big_calls %} calls, {% $fig.big_share %} of them yes, and asks about {% $fig.big_columns %} columns. The {% $fig.zero_rules %} rules whose calls all said no hold {% $fig.zero_calls %} training calls, yet {% $fig.zero_validation_yes %} of the {% $fig.zero_validation %} validation calls that meet them said yes. A rule's counts describe its training calls, and the fewer calls a leaf holds, the further its share can be from that of the clients who reach it later.

Every count can be checked from the rule's conditions alone, on the training calls, which is how the checks test them, and how anyone at the bank can check a rule without the code. A condition that lists the categories a path ruled out holds for every other category, so a client in a category no training call had still meets exactly the rule of the leaf the tree sends them to. Had it named the categories left instead, `default` `unknown` where a path ruled out `no`, that client would meet no rule at all.
