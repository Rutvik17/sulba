from decimal import Decimal


def figures():
    invoices = 8_000
    invoice_in, fields_out = 2_000, 400
    type_minutes, check_minutes = 6, Decimal("1.5")
    to_check = Decimal("0.2")
    checked = int(invoices * to_check)

    def millions(tokens):
        return f"{tokens / 1_000_000:,.1f}".removesuffix(".0") + " million"

    return {
        "invoices": f"{invoices:,}",
        "invoice_in": f"{invoice_in:,}",
        "fields_out": str(fields_out),
        "type_minutes": str(type_minutes),
        "check_minutes": str(check_minutes),
        "to_check": f"{to_check:.0%}",
        "checked": f"{checked:,}",
        "typing_hours": f"{invoices * type_minutes // 60:,}",
        "checking_hours": f"{checked * check_minutes / 60:,.0f}",
        "day_in": millions(invoices * invoice_in),
        "day_out": millions(invoices * fields_out),
    }
