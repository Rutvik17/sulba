import gc
import random

import pytest
from copy_graph import Node, copy_graph

NODES = 100_000


@pytest.fixture(autouse=True)
def unlinked():
    """Unlinks every node when a test ends, so that a long cycle is freed a node at a time."""
    yield
    for each in gc.get_objects():
        if isinstance(each, Node):
            each.neighbours = []


def reached(node):
    """The nodes that node reaches, node first, each once, in the order a search finds them."""
    order, seen, waiting = [], {id(node)}, [node]
    while waiting:
        current = waiting.pop()
        order.append(current)
        for neighbour in current.neighbours:
            if id(neighbour) not in seen:
                seen.add(id(neighbour))
                waiting.append(neighbour)
    return order


def same_shape(original, copy):
    """Whether copy is a copy of original's graph: a new node for each, with the same values
    and links, and no link to an original."""
    pairs = {id(original): copy}
    waiting = [(original, copy)]
    originals = {id(node) for node in reached(original)}
    while waiting:
        node, twin = waiting.pop()
        if twin is node or id(twin) in originals or twin.value != node.value:
            return False
        if len(twin.neighbours) != len(node.neighbours):
            return False
        for neighbour, its_twin in zip(node.neighbours, twin.neighbours):
            if id(neighbour) in pairs:
                if pairs[id(neighbour)] is not its_twin:
                    return False
            else:
                pairs[id(neighbour)] = its_twin
                waiting.append((neighbour, its_twin))
    copies = {id(twin) for twin in pairs.values()}
    return len(copies) == len(pairs) == len(reached(copy))


@pytest.mark.id("tst_r1a2i8")
def test_copy_graph():
    """Copies a small graph with a cycle"""
    one, two, three = Node(1), Node(2), Node(3)
    one.neighbours = [two, three]
    two.neighbours = [three]
    three.neighbours = [one]
    copy = copy_graph(one)
    assert copy is not one and copy.value == 1
    assert [node.value for node in copy.neighbours] == [2, 3]
    assert copy.neighbours[0].neighbours[0] is copy.neighbours[1]
    assert copy.neighbours[1].neighbours[0] is copy
    assert same_shape(one, copy)


@pytest.mark.id("tst_0gdwpn")
def test_edges():
    """Copies nothing for None, a lone node, a node linking to itself, and equal values apart"""
    assert copy_graph(None) is None
    alone = Node(7)
    assert same_shape(alone, copy_graph(alone))
    loop = Node(1)
    loop.neighbours = [loop, loop]
    copy = copy_graph(loop)
    assert copy.neighbours == [copy, copy] and copy is not loop
    first, second = Node(5), Node(5)
    first.neighbours = [second]
    second.neighbours = [first]
    copy = copy_graph(first)
    assert copy.neighbours[0] is not copy and same_shape(first, copy)


@pytest.mark.id("tst_bvwsil")
def test_random():
    """Copies random graphs, shape for shape"""
    rng = random.Random(104)
    for _ in range(300):
        nodes = [Node(rng.randint(0, 3)) for _ in range(rng.randint(1, 15))]
        for node in nodes:
            node.neighbours = [rng.choice(nodes) for _ in range(rng.randint(0, 4))]
        start = rng.choice(nodes)
        assert same_shape(start, copy_graph(start))


@pytest.mark.id("tst_vwhxz7")
def test_long():
    """Copies a long cycle in time"""
    nodes = [Node(place) for place in range(NODES)]
    for place, node in enumerate(nodes):
        node.neighbours = [nodes[(place + 1) % NODES]]
    copy = copy_graph(nodes[0])
    values, current = [], copy
    for _ in range(NODES):
        values.append(current.value)
        current = current.neighbours[0]
    assert values == list(range(NODES)) and current is copy
