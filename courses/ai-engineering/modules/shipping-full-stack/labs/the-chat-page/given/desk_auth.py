"""The desk's sign-in routes: the browser sent to the provider, the person it signs in given a
session of their own, and the session ended when they sign out."""

from dataclasses import dataclass

from fastapi import APIRouter, Request, Response
from fastapi.responses import RedirectResponse
from starlette.concurrency import run_in_threadpool
from starlette.exceptions import HTTPException

from sessions import (
    SESSION_COOKIE,
    SESSION_DAYS,
    SIGN_IN_COOKIE,
    SIGN_IN_MINUTES,
    Sessions,
)
from sign_in import Pending, Provider, SignInError, authorization_url
from tokens import Keys, person_from


@dataclass(frozen=True)
class Registration:
    """The desk as the provider knows it: its id, its secret and its redirect URI, and whether
    its cookies are sent only over HTTPS."""

    client_id: str
    client_secret: str
    redirect_uri: str
    secure: bool


def local(back: str) -> str:
    """The path to send the person back to: back when it's a path on this site, else /. A
    browser reads // or /\\ at the start as another site's address, and drops tabs and line
    breaks before it reads it."""
    if (
        back.startswith("/")
        and not back.startswith(("//", "/\\"))
        and back.isprintable()
    ):
        return back
    return "/"


router = APIRouter(prefix="/auth")


def cookie(
    response: Response,
    registration: Registration,
    name: str,
    value: str,
    seconds: int,
    path: str,
) -> None:
    response.set_cookie(
        name,
        value,
        max_age=seconds,
        path=path,
        secure=registration.secure,
        httponly=True,
        samesite="lax",
    )


@router.get("/sign-in")
def sign_in(request: Request, back: str = "/") -> RedirectResponse:
    """Sends the browser to the provider, and keeps the sign-in until it comes back."""
    registration: Registration = request.app.state.registration
    provider: Provider = request.app.state.provider
    sessions: Sessions = request.app.state.sessions
    pending = Pending.new()
    token = sessions.begin(pending, local(back))
    url = authorization_url(
        provider, registration.client_id, registration.redirect_uri, pending
    )
    response = RedirectResponse(url, status_code=303)
    cookie(response, registration, SIGN_IN_COOKIE, token, SIGN_IN_MINUTES * 60, "/auth")
    return response


@router.get("/callback")
async def callback(request: Request) -> RedirectResponse:
    """The provider's answer: the person signed in, given a new session, and sent back."""
    registration: Registration = request.app.state.registration
    keys: Keys = request.app.state.keys
    sessions: Sessions = request.app.state.sessions
    token = request.cookies.get(SIGN_IN_COOKIE)
    taken = await run_in_threadpool(sessions.take, token) if token else None
    if taken is None:
        raise HTTPException(400, "This sign-in has ended. Sign in again.")
    pending, back = taken
    try:
        person = await person_from(
            keys.client,
            keys,
            client_id=registration.client_id,
            client_secret=registration.client_secret,
            redirect_uri=registration.redirect_uri,
            pending=pending,
            answer=request.query_params,
        )
    except SignInError as error:
        raise HTTPException(400, f"Signing in failed. {error}") from error
    # A session from before the sign-in ends, and the person gets one no one else has seen.
    before = request.cookies.get(SESSION_COOKIE)
    if before:
        await run_in_threadpool(sessions.close, before)
    session = await run_in_threadpool(sessions.open, person)
    response = RedirectResponse(back, status_code=303)
    cookie(response, registration, SESSION_COOKIE, session, SESSION_DAYS * 86_400, "/")
    response.delete_cookie(
        SIGN_IN_COOKIE,
        path="/auth",
        secure=registration.secure,
        httponly=True,
        samesite="lax",
    )
    return response


@router.post("/sign-out", status_code=204)
def sign_out(request: Request, response: Response) -> None:
    """Ends the request's session, in the database and in the browser."""
    registration: Registration = request.app.state.registration
    sessions: Sessions = request.app.state.sessions
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        sessions.close(token)
    response.delete_cookie(
        SESSION_COOKIE,
        path="/",
        secure=registration.secure,
        httponly=True,
        samesite="lax",
    )
