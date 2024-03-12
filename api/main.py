# --- Importation des modules
# -- Fast API 
from fastapi import FastAPI, HTTPException, status, Depends
# OAuth2PasswordBearer est utilisé pour la gestion de l'authentification, OAuth2PasswordRequestForm est utilisé pour la gestion de la requête d'authentification
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
# CORS est utilisé pour la gestion des requêtes CORS 
from fastapi.middleware.cors import CORSMiddleware
# --- SQLAlchemy
from sqlalchemy.orm import Session
# datetime est utilisé pour la gestion des dates
from datetime import datetime, timedelta
# typing.Annotated est utilisé pour la gestion des annotations
from typing import Annotated
import schemas, services

# --- Catégories des endpoints (voir documentations Swagger/redocs)
tags_metadata = [
     {
        "name": "Server",
        "description": "Monitor the server state",
    },
    {
        "name": "Users",
        "description": "Operations with users. The **login** logic is also here.",
    },
    {
        "name": "Deck",
        "description": "Operations with decks.",
    },
    {
        "name": "Card",
        "description": "Operations with cards.",
    }, 
    {
        "name": "Train",
        "description": "Operations with training.",
    },
]

# --- FastAPI app
app = FastAPI(
    title="NotaBene API",
    description="This is the API documentation for the NotaBene project ✨📚",
)

# Migration de la base de données
services.create_database()

# Instance de la base de données
services.get_db()

# --- Configuration CORS
# il est possible de passer un tableau avec les origines autorisées, les méthodes autorisées, les en-têtes autorisés, etc.
# ici, on autorise toutes les origines, les méthodes, les en-têtes, etc car on est en développement, en production, il faudra restreindre ces valeurs
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Configuration de l'authentification
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# --- Routes
# --- Server 
@app.get("/", tags=["Server"])
async def root():
    """
    Cette route permet de vérifier si le serveur est en ligne
    """
    return {"message": "NotaBene API is online, welcome to the API documentation at /docs or /redocs"}

@app.get("/unixTimes", tags=["Server"])
async def read_item():
    """
    Cette route permet de récupérer le temps UNIX
    """
    unix_timestamp = datetime.now().timestamp()
    return {"unixTime": unix_timestamp} 

# --- Users 
@app.post("/token", response_model=schemas.Token, tags=["Users"])
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(services.get_db)
)-> schemas.Token:
    """
    Cette route permet de se connecter et de récupérer un token d'accès, à noter qu'ici : username = email
    @param form_data: OAuth2PasswordRequestForm
    @param db: Session
    @return schemas.Token
    """
    return await services.authenticate_user(db, form_data.username, form_data.password)

@app.post("/addUser/", response_model=schemas.User, tags=["Users"])
async def add_user(
    user: schemas.UserCreate,
    db: Session = Depends(services.get_db)
)-> schemas.User:
    """
    Cette route permet d'ajouter un utilisateur
    @param user: schemas.UserCreate
    @param db: Session
    @return schemas.User
    """
    return await services.add_user(db, user)

@app.get("/getAllUsers/", response_model=list[schemas.User], tags=["Users"])
async def read_users(
    db: Session = Depends(services.get_db)
)-> list[schemas.User]:
    """
    Cette route permet de récupérer tous les utilisateurs
    @param db: Session
    @return list[schemas.User]
    """
    return await services.get_all_users(db)

@app.get("/users/me/", response_model=schemas.User, tags=["Users"])
async def read_users_me(
    current_user: Annotated[schemas.User, Depends(services.get_current_user)]
):
    return current_user

# --- Deck
@app.post("/addDeck/", response_model=schemas.Deck, tags=["Deck"])
async def add_deck(
    deck: schemas.DeckBase,
    current_user: Annotated[schemas.User, Depends(services.get_current_user)],
    db: Session = Depends(services.get_db)
)-> schemas.Deck:
    """
    Cette route permet d'ajouter un deck
    @param deck: schemas.DeckBase
    @param current_user: schemas.User
    @param db: Session
    @return schemas.Deck
    """
    return await services.add_deck(db, deck, current_user)

@app.get("/getAllDecks/", response_model=list[schemas.Deck], tags=["Deck"])
async def read_decks(
    current_user: Annotated[schemas.User, Depends(services.get_current_user)],
    db: Session = Depends(services.get_db)
)-> list[schemas.Deck]:
    """
    Cette route permet de récupérer tous les decks de l'utilisateur connecté
    @param current_user: schemas.User
    @param db: Session
    @return list[schemas.Deck]
    """
    return await services.get_decks(db, current_user)

@app.get("/getDeck/{deck_id}", response_model=schemas.Deck, tags=["Deck"])
async def read_deck(
    deck_id: int,
    current_user: Annotated[schemas.User, Depends(services.get_current_user)],
    db: Session = Depends(services.get_db),
)-> schemas.Deck:
    """
    Cette route permet de récupérer un deck spécifique
    @param deck_id: int
    @param current_user: schemas.User
    @param db: Session
    @return schemas.Deck
    """
    return await services.get_deck(db, deck_id, current_user)

# --- Card
@app.post("/addCard/", response_model=schemas.Card, tags=["Card"])
async def add_card(
    card: schemas.CardBase,
    deck_id: int,
    current_user: Annotated[schemas.User, Depends(services.get_current_user)],
    db: Session = Depends(services.get_db)
)-> schemas.Card:
    """
    Cette route permet d'ajouter une carte à un deck
    @param card: schemas.CardBase
    @param deck_id: int
    @param current_user: schemas.User
    @param db: Session
    @return schemas.Card
    """
    return await services.add_card(db, card, deck_id)

@app.put("/updateCard/{card_id}", response_model=schemas.Card, tags=["Card"])
async def update_card(
    card_id: int,
    current_user: Annotated[schemas.User, Depends(services.get_current_user)],
    state: str = "not memorized" or "memorized" or "in progress", # créer un enum pour les états + faire un schema + gérer les erreurs 
    db: Session = Depends(services.get_db),
)-> schemas.Card:
    """
    Cette route permet de modifier le statut d'une carte
    @param card_id: int
    @param card: schemas.CardBase
    @param current_user: schemas.User
    @param db: Session
    @return schemas.Card
    """
    return await services.update_card(db, card_id, state, current_user)

# --- Train
@app.get("/getRandomCard/{deck_id}", response_model=schemas.Card, tags=["Train"])
async def read_random_card(
    deck_id: int,
    current_user: Annotated[schemas.User, Depends(services.get_current_user)],
    db: Session = Depends(services.get_db),
)-> schemas.Card:
    """
    Cette route permet de récupérer une carte aléatoire d'un deck
    @param deck_id: int
    @param current_user: schemas.User
    @param db: Session
    @return schemas.Card
    """
    return await services.get_random_card(db, deck_id, current_user)