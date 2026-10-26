package panics

import (
	"testing"

	"example/totals"
)

func TestPanics(t *testing.T) {
	t.Run("tst_go0004 Takes the first of no amounts", func(t *testing.T) {
		_ = totals.First(nil)
	})
	t.Run("tst_go0005 Takes the first of two", func(t *testing.T) {
		if totals.First([]int{1, 2}) != 1 {
			t.Error("not the first")
		}
	})
}
