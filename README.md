# DataAccess API

API de gouvernance de donnees : catalogue de datasets, demandes d'acces, instruction des demandes et audit des decisions.

Projet d'examen — Master 1 DSIA, Conception d'API REST avec FastAPI .

---

## Stack technique

| Composant | Choix |
|---|---|
| Framework | FastAPI |
| Validation | Pydantic v2 |
| ORM | SQLAlchemy 2.0 (async, `asyncpg`) |
| Migrations | Alembic |
| Base de donnees | PostgreSQL 15 (production), SQLite en memoire (tests) |
| Authentification | OAuth2 password flow, JWT signes (HS256) |
| Tests | pytest, pytest-asyncio, pytest-cov |
| Conteneurisation | Docker, docker-compose |
| CI | GitHub Actions + Codecov |

---

## Architecture

```
app/
  main.py                  application FastAPI, middlewares, routeurs, /health
  api/routes/              auth, users, datasets, access_requests, audit
  core/
    config.py              configuration (Pydantic Settings)
    security.py            hachage, creation et decodage des JWT
    permissions.py         predicats de roles, get_current_user, require_roles
    errors.py              erreurs applicatives
  db/                      session et base declarative
  models/                  user, role, dataset, access_request, audit_event
  schemas/                 DTO d'entree / sortie
  repositories/            acces aux donnees (pattern Repository)
  middlewares/             request_id, security_headers
  utils/                   pagination, hashing, time
tests/
  unit/                    tests unitaires
  integration/             tests d'integration
alembic/                   migrations
```

**Note sur l'emplacement de `get_current_user`.** cet dependance devais etre dans `app/dependencies/security.py`. L'arborescence imposee par le sujet ne prevoyant pas ce dossier, la dependance a ete placee dans `core/permissions.py`, aux cotes des utilitaires d'habilitation. `core/security.py` reste dedie a la cryptographie pure, sans dependance FastAPI.

---

## Installation

Prerequis : Python 3.11, Docker et Docker Compose.

```bash
git clone https://github.com/mamadoufalll/dataaccess-api.git
cd dataaccess-api

python3 -m venv env
source env/bin/activate

pip install -r requirements.txt
```

---

## Variables d'environnement

```bash
cp .env.example .env
```

| Variable | Role | Defaut |
|---|---|---|
| `POSTGRES_USER` | utilisateur PostgreSQL (docker-compose) | — |
| `POSTGRES_PASSWORD` | mot de passe PostgreSQL (docker-compose) | — |
| `POSTGRES_DB` | nom de la base (docker-compose) | `dataaccess_db` |
| `DATABASE_URL` | URL de connexion applicative | voir `config.py` |
| `SECRET_KEY` | cle de signature des JWT | `change-me-in-production` |
| `DEBUG` | mode debogage | `False` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | duree de vie du token d'acces | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | duree de vie du token de rafraichissement | `7` |

Le fichier `.env` est exclu du depot par `.gitignore`. Aucun secret ne doit etre commite.

---

## Lancement

### Avec Docker

```bash
docker compose up --build
```

L'API ecoute sur `http://localhost:8000`, PostgreSQL sur le port hote `5434`.
Le service `api` ne demarre qu'une fois la base declaree saine (`depends_on: service_healthy`), et expose lui-meme un healthcheck sur `/health`.

### En local

```bash
source env/bin/activate
alembic upgrade head
uvicorn app.main:app --reload
```

### Documentation interactive

- Swagger UI : http://localhost:8000/docs
- ReDoc : http://localhost:8000/redoc
- Sante du service : http://localhost:8000/health

---

## Tests

```bash
pytest
pytest tests/unit -v
pytest --cov=app --cov-report=term-missing
```

Les tests s'executent sur **SQLite en memoire** : `tests/conftest.py` surcharge la dependance `get_db` et recree le schema via `Base.metadata` avant chaque test, puis le supprime. Chaque test part donc d'une base vierge, sans interference et sans PostgreSQL a demarrer.

La surcharge de `get_db` reproduit la gestion transactionnelle reelle (commit en fin de requete, rollback en cas d'erreur), afin que les tests exercent le meme comportement que la production.

PostgreSQL reste la base de production et celle utilisee par les migrations Alembic dans le pipeline CI.

---

## Roles et habilitations

| Role | Droits |
|---|---|
| `producer` | creer et mettre a jour ses fiches dataset, demander la publication |
| `requester` | consulter le catalogue publie, creer une demande d'acces, consulter ses demandes |
| `data_steward` | instruire les demandes de son domaine, approuver ou refuser, publier ou rejeter un dataset |
| `admin` | gerer les utilisateurs, les roles et les domaines, consulter l'audit complet |

L'autorisation est centralisee : aucune route ne contient de test de role en dur. Les habilitations passent par la fabrique de dependances `require_roles()` definie dans `core/permissions.py`.

Le cloisonnement par domaine repose sur le predicat `can_decide_on_dataset()` : un administrateur decide partout, un data steward uniquement sur les datasets de son domaine. Un dataset sans domaine reste instruisible par tout steward, faute de cloisonnement applicable.

---

## Endpoints

### Authentification

| Methode | Chemin | Acces |
|---|---|---|
| `POST` | `/auth/register` | public |
| `POST` | `/auth/login` | public |

### Utilisateurs

| Methode | Chemin | Acces |
|---|---|---|
| `GET` | `/users/me` | authentifie |
| `GET` | `/users/` | admin |
| `PATCH` | `/users/{user_id}` | admin, ou l'interesse pour ses champs non sensibles |

### Datasets

| Methode | Chemin | Acces |
|---|---|---|
| `POST` | `/datasets/` | authentifie |
| `GET` | `/datasets/` | public |
| `GET` | `/datasets/{id}` | authentifie (publie, ou proprietaire) |
| `PATCH` | `/datasets/{id}/submit` | proprietaire |
| `PATCH` | `/datasets/{id}/publish` | data_steward, admin |
| `PATCH` | `/datasets/{id}/reject` | data_steward, admin |

### Demandes d'acces

| Methode | Chemin | Acces |
|---|---|---|
| `POST` | `/access-requests/` | authentifie |
| `GET` | `/access-requests/me` | authentifie |
| `GET` | `/access-requests/pending` | data_steward, admin |
| `PATCH` | `/access-requests/{id}/decision` | data_steward du domaine, admin |

### Audit et sante

| Methode | Chemin | Acces |
|---|---|---|
| `GET` | `/audit/events` | data_steward, admin |
| `GET` | `/health` | public |

---

## Regles metier

- Un dataset doit renseigner `classification`, `purpose`, `retention_days` et `contact` avant d'etre soumis.
- Un producteur ne peut pas publier son propre dataset : il le soumet, un data steward decide.
- La transition de statut est explicite : `draft` puis `submitted` puis `published` ou `rejected`.
- Un demandeur ne peut pas deposer deux demandes actives sur le meme dataset (409).
- Une demande deja instruite ne peut plus etre modifiee (400).
- Un data steward n'instruit que les demandes portant sur les datasets de son domaine ; un administrateur decide partout.
- Le role, le domaine et l'activation d'un compte ne sont modifiables que par un administrateur.
- Toute decision d'approbation ou de refus cree un evenement d'audit.

---

## Codes d'erreur

| Code | Signification |
|---|---|
| `400` | regle metier invalide |
| `401` | non authentifie ou token invalide |
| `403` | authentifie mais non habilite |
| `404` | ressource absente ou non visible |
| `409` | conflit (doublon) |

---

## Migrations

```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
alembic downgrade -1
```

---

## Integration continue

Le workflow `.github/workflows/ci.yml` s'execute a chaque push et pull request sur `main` :

1. installation des dependances (Python 3.11) ;
2. demarrage d'un service PostgreSQL ephemere ;
3. application des migrations Alembic ;
4. execution de pytest avec mesure de couverture ;
5. envoi du rapport a Codecov ;
6. construction de l'image Docker.

Le secret `CODECOV_TOKEN` se declare dans *Settings > Secrets and variables > Actions*.

---

## Limites connues

- **Expiration automatique des demandes.** L'invariant prevoyant qu'une demande expire si sa date de fin est passee n'est pas encore applique.
- **`models/role.py`.** La table `roles` existe mais la source de verite des habilitations est l'enumeration `UserRole` portee par le modele `User`.
- **`utils/pagination.py`.** Le helper `paginate()` est teste unitairement mais n'est pas encore branche dans les routes paginees, qui retournent directement une liste sans compteur total.