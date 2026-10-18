The assistant's tests count the losses, check that the network's arrays change, that the same random numbers train the same network, that the validation digits stay out, and that a network of one array has its gradient clipped. Ask what each would miss.

---

Give `train` your own `loss_and_grads` that notes each batch's pixels, digits and gradients before it hands them back, then check what the batches held, and each step against the one its gradients call for.
