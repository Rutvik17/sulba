import json
import string

import pytest
import regex

from constrain import END, allowed, complete, generate, mask

BOOKING = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "minLength": 1, "maxLength": 12},
        "bike": {"enum": ["road", "mountain", "city", "cargo", "e-bike"]},
        "service": {"enum": ["puncture", "brakes", "gears", "full service"]},
        "day": {
            "enum": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        },
        "bikes": {"type": "integer", "minimum": 1, "maximum": 3},
        "collect": {"type": "boolean"},
    },
    "required": ["name", "bike", "service", "day", "bikes", "collect"],
    "additionalProperties": False,
}
VOCABULARY = [
    END,
    *'{}",:',
    '{"',
    '":"',
    '","',
    '":',
    ',"',
    '"}',
    "name",
    "bike",
    "bikes",
    "service",
    "day",
    "collect",
    "road",
    "mount",
    "ain",
    "mountain",
    "city",
    "cargo",
    "e-",
    "punct",
    "ure",
    "brakes",
    "gears",
    "full",
    " service",
    "Monday",
    "Tuesday",
    "Saturday",
    "Sunday",
    "Wed",
    "nes",
    "true",
    "false",
    "True",
    "null",
    *string.ascii_letters,
    *string.digits,
    "12",
    "10",
    " ",
    "\n",
    "\t",
    "\\",
    "Sure",
    "!",
    " Here",
    "'s",
    " the",
    " booking",
    " Ana",
    "Ana",
    " Silva",
    "Sam",
    "bmx",
    "é",
    "🚲",
]
REPLIES = [
    '{"name":"Ana Silva","bike":"city","service":"brakes","day":"Monday","bikes":1,'
    '"collect":true}',
    '{"name":"Sam","bike":"mountain","service":"full service","day":"Wednesday",'
    '"bikes":3,"collect":false}',
    '{"name":"é🚲","bike":"e-bike","service":"puncture","day":"Saturday","bikes":2,'
    '"collect":false}',
]


def pattern(schema):
    """A regular expression for the replies schema allows: compact JSON, every key in order."""
    if "enum" in schema:
        options = (
            regex.escape(json.dumps(each, ensure_ascii=False))
            for each in schema["enum"]
        )
        return "(?:" + "|".join(options) + ")"
    match schema["type"]:
        case "object":
            keys = (
                regex.escape(("," if number else "") + json.dumps(key) + ":")
                + pattern(each)
                for number, (key, each) in enumerate(schema["properties"].items())
            )
            return r"\{" + "".join(keys) + r"\}"
        case "string":
            least, most = schema["minLength"], schema["maxLength"]
            return rf'"[^"\\\x00-\x1f]{{{least},{most}}}"'
        case "integer":
            values = range(schema["minimum"], schema["maximum"] + 1)
            return "(?:" + "|".join(map(str, values)) + ")"
        case "boolean":
            return "(?:true|false)"


REFERENCE = regex.compile(pattern(BOOKING))


def can_start(text):
    return REFERENCE.fullmatch(text, partial=True) is not None


def whole(text):
    return REFERENCE.fullmatch(text) is not None


def reference_mask(text):
    return [
        whole(text) if token == END else can_start(text + token) for token in VOCABULARY
    ]


def reference_generate(scores, max_tokens):
    text = ""
    for _ in range(max_tokens):
        can, score = reference_mask(text), scores(text)
        best = max((i for i, ok in enumerate(can) if ok), key=lambda i: score[i])
        if VOCABULARY[best] == END:
            return text, "stop"
        text += VOCABULARY[best]
    return text, "length"


def copier(target):
    """A model that wants to write target: it scores each token by how much of the target it
    writes, and the end once it has written all of it."""

    def scores(text):
        return [
            (100 if text == target else 0)
            if token == END
            else (len(token) if target.startswith(text + token) else 0)
            for token in VOCABULARY
        ]

    return scores


def texts():
    """Every start of each reply, and each start with one token more."""
    starts = {reply[:end] for reply in REPLIES for end in range(len(reply) + 1)}
    return sorted(
        starts | {start + token for start in starts for token in VOCABULARY[1:]}
    )


@pytest.mark.id("tst_s1pkxd")
def test_starts():
    """A text is the start of a reply exactly when the schema allows it to go on to one"""
    for text in texts():
        assert allowed(text, BOOKING) == can_start(text), repr(text)


@pytest.mark.id("tst_82vdtq")
def test_whole_replies():
    """A text is a whole reply exactly when the schema allows it as it stands"""
    for text in texts():
        assert complete(text, BOOKING) == whole(text), repr(text)


@pytest.mark.id("tst_7ptyit")
def test_mask():
    """The mask lets through the tokens that keep the reply valid, and the end once it's whole"""
    for reply in REPLIES:
        for end in range(len(reply) + 1):
            assert mask(reply[:end], VOCABULARY, BOOKING) == reference_mask(reply[:end])


@pytest.mark.id("tst_1txfr7")
def test_the_model_s_own_reply():
    """A model that wants to write a valid reply writes it, and stops"""
    for reply in REPLIES:
        assert generate(copier(reply), VOCABULARY, BOOKING, 100) == (reply, "stop")


@pytest.mark.id("tst_ncrefm")
def test_masked_choices():
    """Where the model wants a token the mask refuses, it writes the best one it allows"""
    wants = [
        "Sure! Here's the booking: " + REPLIES[0],
        REPLIES[0].replace("city", "bmx"),
        REPLIES[1].replace('"bikes":3', '"bikes":12'),
        REPLIES[0].replace("Ana Silva", "Ana Silva\nand Sam"),
        REPLIES[0].replace("true", "True"),
    ]
    for target in wants:
        found = generate(copier(target), VOCABULARY, BOOKING, 100)
        assert found == reference_generate(copier(target), 100), repr(target)
        assert found[1] == "stop" and whole(found[0])


@pytest.mark.id("tst_1ss2zx")
def test_cut_off():
    """A reply that reaches max_tokens stops where it is, valid so far but not whole"""
    text, finish_reason = generate(copier(REPLIES[1]), VOCABULARY, BOOKING, 9)
    assert finish_reason == "length"
    assert (text, finish_reason) == reference_generate(copier(REPLIES[1]), 9)
    assert can_start(text) and not whole(text)
    with pytest.raises(json.JSONDecodeError):
        json.loads(text)
