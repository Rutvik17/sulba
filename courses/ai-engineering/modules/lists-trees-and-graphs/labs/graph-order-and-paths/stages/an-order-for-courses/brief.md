A school's `courses` are numbered from 0, and `prerequisites` lists pairs `(course, before)`: `course` can only be taken once `before` has been. Write `course_order`:

```
course_order(courses, prerequisites) -> every course once, in an order that takes each after
    all the courses it needs, or [] if there's no such order
```

With 4 courses and the prerequisites `[(1, 0), (2, 0), (3, 1), (3, 2)]`, both `[0, 1, 2, 3]` and `[0, 2, 1, 3]` will do, and the tests accept any order that does. With `[(0, 1), (1, 0)]`, each course needs the other first, so there's no order. The tests' largest school has {% $fig.courses %} courses, each but the first needing the one before it.
