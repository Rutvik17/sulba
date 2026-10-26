package panics

import (
	"testing"

	"example/gateway"
)

func TestPanics(t *testing.T) {
	t.Run("tst_ffffff first of nothing", func(t *testing.T) {
		_ = gateway.First(nil)
	})
	t.Run("tst_gggggg never runs", func(t *testing.T) {})
}
