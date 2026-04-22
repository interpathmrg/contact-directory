import msal
import structlog

from app.config import get_settings

log = structlog.get_logger()
settings = get_settings()

# MSAL agrega openid/profile automáticamente; solo especificar scopes de recurso
_SCOPES: list[str] = ["User.Read"]

_AUTHORITY = f"https://login.microsoftonline.com/{settings.azure_tenant_id}"


def _get_msal_app() -> msal.ConfidentialClientApplication:
    return msal.ConfidentialClientApplication(
        client_id=settings.azure_client_id,
        client_credential=settings.azure_client_secret,
        authority=_AUTHORITY,
    )


def get_auth_url(state: str) -> str:
    """Genera la URL de autorización de Microsoft para el flujo OAuth2."""
    app = _get_msal_app()
    return app.get_authorization_request_url(
        scopes=_SCOPES,
        redirect_uri=settings.azure_redirect_uri,
        state=state,
    )


def exchange_code_for_token(code: str) -> dict:
    """Intercambia el código de autorización por tokens de Azure AD."""
    app = _get_msal_app()
    result = app.acquire_token_by_authorization_code(
        code=code,
        scopes=_SCOPES,
        redirect_uri=settings.azure_redirect_uri,
    )
    if "error" in result:
        description = result.get("error_description", result.get("error", "Unknown"))
        log.error("azure_token_exchange_failed", error=description)
        raise ValueError(f"Error de Azure AD: {description}")
    return result


def extract_user_info(token_result: dict) -> dict[str, str]:
    """
    Extrae email y nombre de los claims del id_token.
    Azure AD puede usar 'email' o 'preferred_username' dependiendo del tenant.
    """
    claims: dict = token_result.get("id_token_claims", {})
    email: str = (
        claims.get("email")
        or claims.get("preferred_username")
        or ""
    ).lower().strip()
    name: str = claims.get("name", email)

    if not email:
        log.warning("azure_no_email_in_claims", claims_keys=list(claims.keys()))
        raise ValueError("No se pudo obtener el email del token de Azure AD")

    return {"email": email, "name": name}
