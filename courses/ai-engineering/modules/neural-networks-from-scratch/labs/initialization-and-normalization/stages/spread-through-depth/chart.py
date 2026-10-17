import numpy as np

from init import kaiming_uniform

LAYERS, WIDTH, SAMPLES, TOP = 30, 512, 32, 3


def sizes(weights, X):
    """The root mean square of each layer's outputs after its ReLU, as a share of X's."""
    first = np.sqrt(np.mean(X**2))
    found = []
    for weight in weights:
        X = np.maximum(X @ weight.T, 0.0)
        found.append(np.sqrt(np.mean(X**2)) / first)
    return np.array(found)


def shown(values):
    """Each value, or None where it's above the chart's top."""
    return [float(value) if value <= TOP else None for value in values]


def chart(scale):
    rng = np.random.default_rng(0)
    X = rng.normal(size=(SAMPLES, WIDTH))
    shape = (WIDTH, WIDTH)
    kaiming = [
        scale * kaiming_uniform(shape, rng, nonlinearity="relu") for _ in range(LAYERS)
    ]
    bound = 1 / np.sqrt(WIDTH)
    default = [rng.uniform(-bound, bound, size=shape) for _ in range(LAYERS)]
    layers = np.arange(1, LAYERS + 1)
    yours = sizes(kaiming, X)
    return {
        "x": {"min": 0, "max": LAYERS, "step": 5, "label": "layer"},
        "y": {
            "min": 0,
            "max": TOP,
            "step": 0.5,
            "label": "size, as a share of the input's",
        },
        "lines": [
            {
                "style": "dashed",
                "label": "c to the power of the layer",
                "x": layers,
                "y": shown(scale**layers),
            },
            {
                "style": "base",
                "label": "nn.Linear's start",
                "x": layers,
                "y": shown(sizes(default, X)),
            },
            {
                "style": "main",
                "label": "Your Kaiming start, its range times c",
                "x": layers,
                "y": shown(yours),
            },
        ],
        "points": [],
        "readouts": [
            {
                "label": f"Size after {LAYERS} layers",
                "value": f"{yours[-1]:.3g} of the input's",
            }
        ],
        "description": (
            f"The size of the signal through {LAYERS} layers of {WIDTH} ReLUs, started with "
            f"your Kaiming start times {scale:g} and with nn.Linear's"
        ),
    }
