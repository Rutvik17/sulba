An accounting firm receives {% $fig.invoices %} supplier invoices a day for its clients, as PDFs and photos. Staff type each into the ledger: the supplier, the date, the invoice number, the lines, the tax and the total. The firm wants the fields read automatically, with staff checking only the invoices that need it.

Design it. Take these as given:

- an invoice's text, with the instructions, is about {% $fig.invoice_in %} tokens, and its fields about {% $fig.fields_out %};
- staff take about {% $fig.type_minutes %} minutes to type an invoice and {% $fig.check_minutes %} to check one;
- about {% $fig.to_check %} of invoices fail a check or come from a new supplier.
