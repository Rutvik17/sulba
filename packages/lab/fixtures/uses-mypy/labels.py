from boxes import Box


def label(box):
    return f"{box.width} by {box.height}"


def widest(boxes: list[Box]) -> str:
    return max(box.width for box in boxes)
