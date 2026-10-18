Each of the assistant's tests checked something a wrong script gets right too: how many losses came back, that the arrays changed, that the same random numbers gave the same network, that the validation digits stayed out, and that one array's gradient was clipped. None looked at what a batch held, or compared a step with the gradients it came from.

---

The checks ran the script with a `loss_and_grads` of their own, which noted every batch and the gradients it gave, and pixels with each digit's row number after them. From those they could see which rows each batch came from, whether each digit was its own pixels', and whether each step was the one its gradients call for. A training loop can't hide what it trains on from the function that gives it its gradients, so the same check works on any loop that takes its gradients from a function it's given.
