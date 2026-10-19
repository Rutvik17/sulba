The assistant's tests ran each part once, on a few tiles. Every score has its shape, the warm-up leaves the backbone's weights as they were, and fine-tuning changes them, all with the four problems in the code: none of them raises an error, and the training still runs.

---

Review fine-tuning by what each line asks of the backbone. The rate each parameter learns at is set by the optimizer's groups. Which parameters work out gradients is set by `requires_grad`, whatever the optimizer holds. The classifier must be given tiles the same way in training as in use, and the names given to its outputs must follow the numbers it was trained with.

Fine-tuning runs every tile forward and back through the backbone at every epoch, about three times the work of a forward pass each time, where a probe needs the backbone's features of each tile once.
