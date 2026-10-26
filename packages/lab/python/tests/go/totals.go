// Package totals adds up a bill.
package totals

import (
	"errors"
	"fmt"
	"time"
)

// Sum adds the amounts, in cents.
func Sum(amounts []int) int {
	total := 0
	for _, amount := range amounts {
		total += amount
	}
	return total
}

// Dollars shows cents as dollars and cents.
func Dollars(cents int) string {
	return fmt.Sprintf("%d.%d", cents/100, cents%100)
}

// First is the first of the amounts.
func First(amounts []int) int {
	return amounts[0]
}

// ErrClosed is the error Wait gives once the till is closed.
var ErrClosed = errors.New("the till is closed")

// Wait waits for the till to open, a second, or gives ErrClosed if closed.
func Wait(closed bool) error {
	if closed {
		return ErrClosed
	}
	time.Sleep(time.Second)
	return nil
}
