`client_secret: SecretStr` keeps the secret out of the settings' repr and JSON, and `settings.client_secret.get_secret_value()` gives it where it's needed.

---

`FastAPI(dependencies=[Depends(check)])` runs `check` before every route, and a check that raises `HTTPException(403, ...)` refuses the request.

---

`JOIN conversations ON conversations.id = turns.conversation_id WHERE conversations.owner = %s` keeps a person's turns alone.
