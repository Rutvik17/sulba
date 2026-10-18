import pytest
from torch.optim.optimizer import register_optimizer_step_post_hook

from data import batches, evaluate, sets
from run import run

PATH = "data/digits.csv"


@pytest.mark.id("tst_rrjrx5")
def test_two_epochs(tmp_path):
    """Two epochs, read in evaluation mode"""
    train, validation, _ = sets(PATH)
    reader = run(tmp_path / "run.pt", train, validation, epochs=2)
    assert not any(module.training for module in reader.modules())
    _, right = evaluate(reader, validation)
    assert right >= 0.9 * len(validation)


@pytest.mark.id("tst_9k3ua5")
def test_picked_up(tmp_path):
    """Saved at its path, and picked up from there"""
    train, validation, _ = sets(PATH)
    path = tmp_path / "run.pt"
    run(path, train, validation, epochs=1)
    assert path.exists()
    steps = []
    hook = register_optimizer_step_post_hook(
        lambda optimizer, args, kwargs: steps.append(1)
    )
    try:
        run(path, train, validation, epochs=2)
    finally:
        hook.remove()
    assert len(steps) == len(batches(train, 0))
