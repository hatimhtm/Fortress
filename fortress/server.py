"""FastAPI server for Fortress.

Exposes the same primitives as the CLI over HTTP so anything that can do
POST/GET can ask for a password (or check one). Lazy imports so FastAPI is
truly optional — install via `pip install 'fortress[server]'`.
"""

import dataclasses


def create_app():
    """Build the FastAPI application."""
    try:
        from fastapi import FastAPI, HTTPException
        from pydantic import BaseModel, Field
    except ImportError as exc:
        raise ImportError(
            "FastAPI is required for server mode. " "Install with: pip install 'fortress[server]'"
        ) from exc

    from fortress import __version__
    from fortress.core import (
        HIBPError,
        PasswordConfig,
        crack_times,
        entropy_of_random,
        estimate_entropy,
        generate_passphrase,
        generate_password,
        generate_pin,
        is_common,
        pwned_count,
        strength_label,
    )
    from fortress.core.wordlist import bits_per_word

    app = FastAPI(
        title="Fortress",
        version=__version__,
        description=(
            "Cryptographically secure password / passphrase / PIN generator. "
            "Every endpoint returns the password plus entropy, strength, and crack-time scenarios."
        ),
    )

    # ── Schemas ─────────────────────────────────────────────────

    class CrackTimesOut(BaseModel):
        online_throttled: str
        online_unthrottled: str
        offline_slow_hash: str
        offline_fast_hash: str
        offline_specialized: str

    class PasswordOut(BaseModel):
        password: str
        length: int
        charset_size: int
        entropy_bits: float
        strength: str
        crack_times: CrackTimesOut

    class PassphraseOut(BaseModel):
        passphrase: str
        word_count: int
        entropy_bits: float
        strength: str
        crack_times: CrackTimesOut

    class PinOut(BaseModel):
        pin: str
        length: int
        entropy_bits: float

    class CheckIn(BaseModel):
        password: str = Field(..., min_length=1)
        pwned: bool = False

    class CheckOut(BaseModel):
        length: int
        entropy_bits: float
        strength: str
        is_common: bool
        pwned_count: int | None = None
        pwned_error: str | None = None
        crack_times: CrackTimesOut

    # ── Helpers ─────────────────────────────────────────────────

    def _ct(entropy: float) -> CrackTimesOut:
        return CrackTimesOut(**dataclasses.asdict(crack_times(entropy)))

    # ── Routes ──────────────────────────────────────────────────

    @app.get("/healthz")
    def healthz() -> dict:
        return {"status": "ok", "version": __version__}

    @app.post("/v1/generate", response_model=PasswordOut)
    def post_generate(
        length: int = 20,
        no_uppercase: bool = False,
        no_lowercase: bool = False,
        no_digits: bool = False,
        no_symbols: bool = False,
        exclude_ambiguous: bool = False,
        no_repeat: bool = False,
    ) -> PasswordOut:
        try:
            config = PasswordConfig(
                length=length,
                use_uppercase=not no_uppercase,
                use_lowercase=not no_lowercase,
                use_digits=not no_digits,
                use_symbols=not no_symbols,
                exclude_ambiguous=exclude_ambiguous,
                no_repeat=no_repeat,
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

        password = generate_password(config=config)
        charset_size = len(config.charset())
        entropy = entropy_of_random(len(password), charset_size)
        label, _ = strength_label(entropy)
        return PasswordOut(
            password=password,
            length=len(password),
            charset_size=charset_size,
            entropy_bits=round(entropy, 2),
            strength=label,
            crack_times=_ct(entropy),
        )

    @app.post("/v1/passphrase", response_model=PassphraseOut)
    def post_passphrase(
        words: int = 6,
        separator: str = "-",
        capitalize: bool = False,
        add_number: bool = False,
        add_symbol: bool = False,
    ) -> PassphraseOut:
        if words < 1:
            raise HTTPException(status_code=422, detail="words must be >= 1")
        phrase = generate_passphrase(
            word_count=words,
            separator=separator,
            capitalize=capitalize,
            add_number=add_number,
            add_symbol=add_symbol,
        )
        entropy = words * bits_per_word() + (3.32 if add_number else 0) + (5.0 if add_symbol else 0)
        label, _ = strength_label(entropy)
        return PassphraseOut(
            passphrase=phrase,
            word_count=words,
            entropy_bits=round(entropy, 2),
            strength=label,
            crack_times=_ct(entropy),
        )

    @app.post("/v1/pin", response_model=PinOut)
    def post_pin(length: int = 6) -> PinOut:
        try:
            p = generate_pin(length)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        entropy = entropy_of_random(length, 10)
        return PinOut(pin=p, length=length, entropy_bits=round(entropy, 2))

    @app.post("/v1/check", response_model=CheckOut)
    def post_check(body: CheckIn) -> CheckOut:
        entropy = estimate_entropy(body.password)
        label, _ = strength_label(entropy)
        hits: int | None = None
        error: str | None = None
        if body.pwned:
            try:
                hits = pwned_count(body.password)
            except HIBPError as exc:
                error = str(exc)
        return CheckOut(
            length=len(body.password),
            entropy_bits=round(entropy, 2),
            strength=label,
            is_common=is_common(body.password),
            pwned_count=hits,
            pwned_error=error,
            crack_times=_ct(entropy),
        )

    return app


def run(host: str = "0.0.0.0", port: int = 8000) -> None:
    """Start the server. Used by the CLI's `serve` command."""
    try:
        import uvicorn
    except ImportError as exc:
        raise ImportError(
            "uvicorn is required for server mode. " "Install with: pip install 'fortress[server]'"
        ) from exc

    uvicorn.run(create_app(), host=host, port=port)
