The app's team asked an assistant for causal self-attention in GPT-2's layout, with the query, key and value layers in one, so that the model can later load GPT-2's weights. The assistant wrote `self_attention.py`, with `CausalSelfAttention(width, heads, dropout=0.1)`. Its dropout sets a share of the weights to 0 at random while the model trains, so that it doesn't lean on any one token. Its four tests all pass.

Review it as if it were about to go into the app's model: fix every problem you can find, and keep what it does right. Four hidden checks test it the way the app will use it. A run shows how many pass. You see which ones when you finish the review.

What the code must do:

- attend in each head as `F.scaled_dot_product_attention` does;
- let no token see a later token;
- give each story in a batch, with padding after each story, the outputs it gets alone;
- once the model is in use, in evaluation mode after `.eval()`, give the same output for the same story every time.
