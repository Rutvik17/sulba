`heights` is a grid of heights, a list of rows. The Pacific touches the grid's top and left edges and the Atlantic its bottom and right. Rain on a square flows to each neighbour, up, down, left or right, that's no higher, and from a square on an edge into the ocean that edge touches. Write `both_oceans`:

```
both_oceans(heights) -> every square (row, column) whose rain can reach both oceans, sorted
```

With this grid it returns `[(0, 4), (1, 3), (1, 4), (2, 2), (3, 0), (3, 1), (4, 0)]`:

```
1 2 2 3 5
3 2 3 4 4
2 4 5 3 1
6 7 1 4 5
5 1 1 2 4
```

The tests' largest grid is {% $fig.side %} by {% $fig.side %}.
