import re
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import Field, field_validator
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    invalid_token_error,
    verify_password,
)
from app.db.dependencies import get_db_session
from app.db.users import UserRecord, create_user, get_user_by_email, get_user_by_id
from app.domain.uml.models import DomainModel

router = APIRouter(prefix="/auth", tags=["auth"])
database_session = Depends(get_db_session)
bearer_scheme = HTTPBearer(auto_error=False)
bearer_credentials = Depends(bearer_scheme)
_EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


class CredentialsRequest(DomainModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        email = value.strip().lower()
        if not _EMAIL_PATTERN.fullmatch(email):
            raise ValueError("email must be valid")
        return email


class AuthUser(DomainModel):
    id: UUID
    email: str


class AccessTokenResponse(DomainModel):
    access_token: str = Field(alias="accessToken")
    token_type: str = Field(default="bearer", alias="tokenType")
    user: AuthUser


def _user_response(user: UserRecord) -> AuthUser:
    return AuthUser(id=user.id, email=user.email)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = bearer_credentials,
    session: Session = database_session,
) -> UserRecord:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise invalid_token_error()
    user = get_user_by_id(session, decode_access_token(credentials.credentials))
    if user is None:
        raise invalid_token_error()
    return user


current_user_dependency = Depends(get_current_user)


@router.post("/register", response_model=AccessTokenResponse, status_code=status.HTTP_201_CREATED)
def register(
    request: CredentialsRequest, session: Session = database_session
) -> AccessTokenResponse:
    if get_user_by_email(session, request.email) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "AUTH_EMAIL_ALREADY_REGISTERED",
                "message": "Email is already registered",
            },
        )
    try:
        user = create_user(session, request.email, hash_password(request.password))
    except IntegrityError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "AUTH_EMAIL_ALREADY_REGISTERED",
                "message": "Email is already registered",
            },
        ) from error
    except SQLAlchemyError as error:
        session.rollback()
        raise HTTPException(
            status_code=503,
            detail={"code": "AUTH_UNAVAILABLE", "message": "Authentication is unavailable"},
        ) from error
    return AccessTokenResponse(accessToken=create_access_token(user.id), user=_user_response(user))


@router.post("/login", response_model=AccessTokenResponse)
def login(request: CredentialsRequest, session: Session = database_session) -> AccessTokenResponse:
    user = get_user_by_email(session, request.email)
    if user is None or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "AUTH_INVALID_CREDENTIALS",
                "message": "Email or password is incorrect",
            },
        )
    return AccessTokenResponse(accessToken=create_access_token(user.id), user=_user_response(user))


@router.get("/me", response_model=AuthUser)
def current_user(user: UserRecord = current_user_dependency) -> AuthUser:
    return _user_response(user)
