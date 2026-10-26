package vetbad

import "fmt"

// Say formats a count wrongly.
func Say() string { return fmt.Sprintf("%d items", "three") }
