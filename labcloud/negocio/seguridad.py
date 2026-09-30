"""Hash de contraseñas (PBKDF2) y generación de tokens de sesión."""

import hashlib
import hmac
import secrets

ITERACIONES = 200_000


def hash_password(password: str) -> str:
    sal = secrets.token_hex(16)
    derivada = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(sal), ITERACIONES)
    return f"pbkdf2_sha256${ITERACIONES}${sal}${derivada.hex()}"


def verificar_password(password: str, almacenado: str) -> bool:
    try:
        _, iteraciones, sal, esperado = almacenado.split("$")
    except ValueError:
        return False
    derivada = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(sal), int(iteraciones))
    return hmac.compare_digest(derivada.hex(), esperado)


def generar_token() -> str:
    return secrets.token_urlsafe(32)
