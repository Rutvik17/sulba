def addresses(digits):
    found, parts = [], []

    def extend(start):
        if len(parts) == 4:
            if start == len(digits):
                found.append(".".join(parts))
            return
        for end in range(start + 1, min(start + 3, len(digits)) + 1):
            part = digits[start:end]
            if (len(part) > 1 and part[0] == "0") or int(part) > 255:
                break
            parts.append(part)
            extend(end)
            parts.pop()

    extend(0)
    return found
