## What it must do

Put each invoice's fields in the ledger correctly, and send to staff the ones that need a person, so that staff time goes where it's needed. A wrong amount in a ledger costs more than a slow one, so every number that goes in must be checked by something.

## Reading

Each file's text comes from the PDF, or from the photo through text recognition. The model reads it into the ledger's schema as structured output: the supplier, the date, the invoice number, each line with its amount, the tax and the total. Amounts are exact decimals and dates are dates, so nothing is rounded or read the wrong way round.

## Checks

The invoice checks itself, and code does the checking:

- the lines add up to the subtotal;
- the tax is the subtotal at the tax's rate;
- the total is the subtotal and the tax;
- the supplier is known to the client, and the invoice number has the supplier's usual form.

## Who checks what

Staff check every invoice that fails a check, comes from a new supplier, or is above an amount the firm sets. The rest goes in, and staff check a sample of them each day. The rules are the firm's to set and to see, not the model's confidence, which isn't a measure of whether a field is right.

## Duplicates

The supplier, the invoice number and the total identify an invoice. A second invoice with the same three, from any channel, is held as a duplicate for staff, not entered twice.

## Evidence

Each entry keeps its source file and the fields as read, and staff's changes to them. The ledger can show where each number came from, and the changes become the next test set.

## Measuring

A set of invoices staff typed by hand, from many suppliers, measures accuracy field by field: an invoice can have a right total and a wrong date. Each day's corrections, by supplier, show where reading has gone wrong.

## What it saves

Typing all {% $fig.invoices %} invoices takes {% $fig.typing_hours %} hours a day. With {% $fig.to_check %} sent to staff, {% $fig.checked %} invoices, checking takes {% $fig.checking_hours %} hours. The model reads {% $fig.day_in %} tokens and writes {% $fig.day_out %} a day.

## The follow-up questions

- **Lines that don't add up:** the check fails and the invoice goes to staff with the fields as read and the file beside them. It could be the reading or the supplier's mistake, and staff decide which.
- **Twice, by email and by post:** the second has the same supplier, number and total, and is held as a duplicate.
- **A new layout:** that supplier's invoices start failing checks or being corrected by staff, which the daily corrections by supplier show within a day.
