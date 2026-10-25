A team of `people`, numbered from 0, is to be split into two groups, and `dislikes` lists pairs of people, `(a, b)`, who mustn't be in the same group. Write `two_groups`:

```
two_groups(people, dislikes) -> whether the people can be split into two groups with no pair
    from dislikes in one group
```

With 4 people and the dislikes `[(0, 1), (0, 2), (1, 3)]`, they can: one group is 0 and 3, the other 1 and 2. With 3 people who all dislike each other, `[(0, 1), (1, 2), (0, 2)]`, they can't. A group may be empty, and a person in a pair with themselves can't be placed. The tests' largest team has {% $fig.people %} people.
