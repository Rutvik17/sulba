A batch norm after each convolution, in place of its bias, makes each layer's gradients depend less on the scale of the weights before it, which lets a network train at a higher learning rate without diverging. In evaluation mode it normalizes by its running estimates, so a photo reads alone as it does among others.

A one-cycle schedule, `torch.optim.lr_scheduler.OneCycleLR`, starts the learning rate at a {% $fig.start %}th of its peak and raises it along a cosine to the peak over the first {% $fig.rise %} of the steps, then lowers it along a cosine to a {% $fig.end %}th of where it started. It moves the momentum the other way, from {% $fig.momentum_high %} down to {% $fig.momentum_low %} at the peak and back, in place of the momentum the optimizer was made with.

The solution keeps stage 3's two convolutions, puts a batch norm after each in place of its bias, and trains them by SGD on a one-cycle schedule with a peak learning rate of {% $fig.peak %}. Its network does {% $fig.macs %} multiply-adds a photo, {% $fig.share %} of the budget.

The check reads the test photos for the shop. Choices made by watching that score fit the test photos, which then no longer measure how the classifier does on photos it hasn't seen: try choices on photos held out of the training set.
