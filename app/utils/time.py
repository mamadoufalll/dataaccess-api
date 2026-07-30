import datetime

def utcnow() -> datetime.datetime:
    """Retourne la date/heure UTC actuelle (timezone-aware)."""
    return datetime.datetime.now(datetime.UTC)

def utcnow_naive() -> datetime.datetime:
    """Retourne la date/heure UTC actuelle (naive, pour compatibilité SQLite)."""
    return datetime.datetime.utcnow()
