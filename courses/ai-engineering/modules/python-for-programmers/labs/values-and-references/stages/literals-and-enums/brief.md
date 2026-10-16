The form sends some fields as one of a few values, such as the side a sample was taken from. superstruct's `literal` passes one value only, and `enums` any of a list:

```js
(value) => value === constant || `Expected the literal \`${description}\`, but received: ${print(value)}`
(value) => values.includes(value) || `Expected one of \`${description}\`, but received: ${print(value)}`
```

JavaScript's `===` is strict: values of different types are never equal, two numbers are equal when their values are, and an object or an array is equal only to itself. `includes` compares as `===` does, except that it finds NaN in a list that holds it.

Python has two comparisons, and neither is `===`. `a == b` asks whether two values are equal, and `True == 1` holds, since `bool` is a subclass of `int`. `a is b` asks whether they are the same object, and two equal numbers or strings can be different objects. Write:

```
same(a, b) -> whether JavaScript's a === b would be true, for values JSON gives
literal(value, constant) -> None when value === constant
enums(value, options) -> None when options.includes(value)
```

with superstruct's messages, which list the options with commas between them:

```
Expected the literal `42`, but received: False
Expected one of `'one','two'`, but received: 'invalid'
```
