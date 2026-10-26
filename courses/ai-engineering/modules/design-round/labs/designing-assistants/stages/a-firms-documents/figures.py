from decimal import ROUND_HALF_UP, Decimal


def dollars(amount, places="0.01"):
    return f"${Decimal(amount).quantize(Decimal(places), rounding=ROUND_HALF_UP):,}"


def millions(tokens):
    return f"{Decimal(tokens) / 1_000_000:,.1f}".removesuffix(".0") + " million"


def figures():
    documents, per_document = 400_000, 6
    dimensions, number_bytes, half_bytes = 768, 4, 2
    later = 5_000_000
    passages = documents * per_document
    vector_bytes = dimensions * number_bytes

    def gigabytes(count, size):
        return f"{count * size / 1e9:.1f} GB"

    return {
        "staff": "2,000",
        "documents": f"{documents:,}",
        "per_document": str(per_document),
        "dimensions": str(dimensions),
        "number_bytes": str(number_bytes),
        "half_bytes": str(half_bytes),
        "changes": "3,000",
        "questions": "10,000",
        "passages": f"{passages:,}",
        "vector_bytes": f"{vector_bytes:,}",
        "vector_gb": gigabytes(passages, vector_bytes),
        "half_gb": gigabytes(passages, dimensions * half_bytes),
        "later_passages": f"{later:,}",
        "later_gb": gigabytes(later, vector_bytes),
        "cache_seconds": "60",
        "leaves_at": "10:00",
    }
