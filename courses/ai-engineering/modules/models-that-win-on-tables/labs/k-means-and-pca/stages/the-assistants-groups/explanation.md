The assistant's tests checked that the scaled measurements have a mean of 0, that the plot's two directions have length 1 and meet at right angles, that each group's name is a variety among its beans, and that every harvest bean gets a name. None compared the directions with those that vary most, scored the training beans with the model that grouped them, counted the varieties within each group, or asked whose centres a harvest bean joined.

---

Everything a grouping knows comes from the training beans: the statistics that scale a bean, the centres of its groups, and the names they carry. A bean seen later is scaled by those statistics and joins the group of the nearest of those centres. A new k-means on a new batch finds groups of its own and numbers them afresh, so the training groups' names don't apply to them.
