The take-home's example stay gets a probability of {% $fig.probability %}, under the threshold of {% $fig.threshold %}, so its `call` is {% $fig.call %}.

FastAPI reads each request's JSON into a `Stay` before `predict` runs. A field missing, or a value its field can't take, such as a stay of no days or a code the mapping doesn't list, gets a 422 whose `detail` names the field, and the model never sees it. The codes the mapping lists that no stay in the extract has are taken, since the encoder answers from the stay's other fields, as stage 5 checked. The deaths and hospice care are refused: the model learned from no such stays, as the study behind the extract left them out.

With `Prediction` as `predict`'s return type, FastAPI checks each answer against it, and the API's schema describes the answer as well as the request. FastAPI serves that schema at `/openapi.json`, and a page of it at `/docs`, so a tool built for the planners can read what the service takes and gives.

`trained` is loaded once, as `app.py` is imported, so a request only encodes one row and scores it.
