`table.createCaption()`, `table.createTHead()`, `table.createTBody()` and `table.createTFoot()` make a table's parts, and `section.insertRow()` a row in one.

---

`new Intl.NumberFormat('en-US', { style: 'percent' })`, `{ style: 'unit', unit: 'second', maximumFractionDigits: 1 }` and `{ style: 'currency', currency: 'USD', minimumFractionDigits: 2, maximumFractionDigits: 4 }` format the shares, times and costs. Make each once and use it for every cell.

---

`Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate())` is the start of today in UTC, in milliseconds. A day earlier is 24 hours less, and `toISOString().slice(0, 10)` writes it as the desk does.
