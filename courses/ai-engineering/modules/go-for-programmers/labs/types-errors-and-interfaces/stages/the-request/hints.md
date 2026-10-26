A struct tag names a field in JSON, after its type: ``MaxTokens int `json:"max_tokens,omitempty"` ``.

---

`fmt.Errorf("%w: %w", ErrNotJSON, err)` wraps both errors, so `errors.Is` finds the first and `errors.AsType` finds the type of the second.

---

`errors.AsType[*json.UnmarshalTypeError](err)` gives json's error for a value of the wrong type, and its `Field` is the field's path, such as `messages.0.content`. A body that's a JSON array gives one too, with no field.

---

After `decoder.Decode`, `decoder.More()` reports whether anything but space is left.
