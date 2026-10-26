package ledger

import "fmt"

// Receipt gives a line for each amount, in cents, shown as dollars and cents, then the total.
func Receipt(cents []int) []string {
	lines := make([]string, 0, len(cents)+1)
	total := 0
	for _, each := range cents {
		lines = append(lines, dollars(each))
		total += each
	}
	return append(lines, "Total "+dollars(total))
}

func dollars(cents int) string {
	return fmt.Sprintf("%d.%02d", cents/100, cents%100)
}
