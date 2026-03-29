from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas, auth

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=schemas.TokenResponse)
def login(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    username = payload.username.strip().capitalize()
    user = db.query(models.User).filter(models.User.username == username).first()

    if not user or not auth.verify_password(payload.password, user.password or ""):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    token = auth.create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer", "username": user.username}


@router.post("/signup", response_model=schemas.TokenResponse, status_code=201)
def signup(payload: schemas.SignupRequest, db: Session = Depends(get_db)):
    username = payload.username.strip().capitalize()

    if db.query(models.User).filter(models.User.username == username).first():
        raise HTTPException(status_code=409, detail=f"Username '{username}' already exists")

    hashed = auth.hash_password(payload.password)
    user   = models.User(username=username, password=hashed)
    db.add(user)
    db.flush()

    # Default vault
    db.add(models.Vault(vault_name="Main", user_id=user.user_id, balance=0.0))

    # Default settings
    for key, value in [("currency", "EGP"), ("theme", "dark"), ("default_vault", "Main")]:
        db.add(models.Setting(user_id=user.user_id, key=key, value=value))

    db.commit()

    token = auth.create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer", "username": user.username}


@router.get("/me", response_model=schemas.UserResponse)
def get_me(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(__import__("app.dependencies", fromlist=["get_current_user"]).get_current_user),
):
    return current_user
