When the copy of a node's neighbour is needed, it may already exist, made when another node linked to the same neighbour. How do you find it, so each node is copied once and cycles end?

---

Keep a dict from each original node to its copy. Visit nodes from a list: for each neighbour, make its copy if the dict has none and add it to the list, then link the node's copy to the neighbour's copy.
