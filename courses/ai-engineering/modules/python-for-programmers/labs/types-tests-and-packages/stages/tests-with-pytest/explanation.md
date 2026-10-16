```python
@pytest.mark.parametrize("value", [True, False, math.nan, "17.99", None])
def test_number_fails(value):
    with pytest.raises(StructError):
        create(value, number())


@pytest.mark.parametrize("value", [[17.99, "3"], ["3", 17.99], (17.99, 3), "17.99"])
def test_array_fails(value):
    with pytest.raises(StructError):
        create(value, array(number()))
```

A test shows a bug only when it fails with the bug in place. A struct that fails nothing passes every test of the values that pass, so the values that should fail carry most of the weight: the edges JavaScript and Python draw differently, such as `True`, and the cases a shortcut would miss, such as a bad second item.

A broken copy that every test passes on marks behaviour nothing tests. Breaking code on purpose and running the tests against it is called mutation testing, and tools such as mutmut do it across a whole project.
