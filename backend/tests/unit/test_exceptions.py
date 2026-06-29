from fastapi import status
from app.core.exceptions import (
    NotFoundError,
    ValidationError,
    AuthenticationError,
    EncryptionError,
)

def test_exception_status_codes():
    assert NotFoundError("").status_code == status.HTTP_404_NOT_FOUND
    assert ValidationError("").status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert AuthenticationError("").status_code == status.HTTP_401_UNAUTHORIZED
    assert EncryptionError("").status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
