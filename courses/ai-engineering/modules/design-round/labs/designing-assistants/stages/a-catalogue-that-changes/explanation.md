## What it must do

Help a customer choose food and fill their basket, with every price and every claim of stock true at the moment it's shown, and nothing added to the basket that the customer didn't choose.

## Model and systems

The model is good at understanding what a customer wants and at suggesting what to cook. It can't know a price or what's in stock now, and must never guess them. So the assistant has tools, as in Tools, streaming and MCP:

- `search_products(query)`: the catalogue's own search, returning products with their ids, sizes, prices and stock now;
- `find_recipes(query)`: a search over an index of recipes, which change rarely;
- `propose_basket_change(product_id, quantity)`: a proposal, shown to the customer, that changes nothing yet.

## A turn

1. The model reads the question and the chat, and calls the tools it needs: often a recipe search, then a product search for its ingredients.
2. Code checks each product id the model picks: it exists, it's in stock, and its price is the one the search returned.
3. The answer streams to the customer, each product shown with its size and price as cards built from the catalogue, not as text the model wrote.
4. A proposed change shows the product, its size, the quantity and the price, and a button to add it. Only the customer's press changes the basket.

## Prices and checkout

A price in the chat is the price when it was given, and says so. Checkout prices the basket again from the catalogue, so the customer pays the current price, and a price that changed since the chat is shown before they pay.

## Speed

{% $fig.customers %} customers asking {% $fig.turns %} questions each make {% $fig.turns_day %} questions a day. Each tool call adds about {% $fig.search_ms %} milliseconds, so the design allows {% $fig.max_calls %} tool calls a turn, at most {% $fig.max_tool_ms %} milliseconds if none could run side by side, runs independent searches at once, and streams the answer as it's written.

## Tests

A test set of conversations, each with the products and quantities a person would choose, runs on every change to the prompt, the tools or the model. It checks the products chosen, the quantities, and that every price and every claim of stock in an answer came from a tool's result in the same turn.

## The follow-up questions

- **A price changes mid-answer:** the customer sees the price the search returned, labelled as the price then, and pays the price at checkout, where any change is shown first.
- **An out-of-stock suggestion:** the stock came from somewhere other than the search in that turn, such as the model's memory or an old index. The fix is the check: every product shown is checked against the catalogue in the same turn.
- **Twelve boxes of eggs:** quantities are in the product's own unit, and a box of {% $fig.dozen %} is one. The proposal shows "1 box of {% $fig.dozen %}" before anything changes, and a quantity above the usual for a product asks the customer again.
