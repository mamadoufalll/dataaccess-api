import datetime

from app.utils.hashing import hash_password, verify_password
from app.utils.pagination import PaginatedResponse, paginate
from app.utils.time import utcnow, utcnow_naive


class TestHashing:
    def test_le_hash_differe_du_mot_de_passe(self):
        h = hash_password("motdepasse")
        assert h != "motdepasse"
        assert len(h) > 20

    def test_verification_accepte_le_bon_mot_de_passe(self):
        h = hash_password("motdepasse")
        assert verify_password("motdepasse", h) is True

    def test_verification_refuse_un_mauvais_mot_de_passe(self):
        h = hash_password("motdepasse")
        assert verify_password("mauvais", h) is False

    def test_deux_hachages_du_meme_mot_de_passe_different(self):
        assert hash_password("secret") != hash_password("secret")


class TestPagination:
    def test_paginate_encapsule_les_items(self):
        resultat = paginate(items=["a", "b"], total=10, skip=0, limit=2)
        assert isinstance(resultat, PaginatedResponse)
        assert resultat.items == ["a", "b"]
        assert resultat.total == 10
        assert resultat.skip == 0
        assert resultat.limit == 2

    def test_paginate_accepte_une_liste_vide(self):
        resultat = paginate(items=[], total=0, skip=0, limit=20)
        assert resultat.items == []
        assert resultat.total == 0


class TestTime:
    def test_utcnow_est_timezone_aware(self):
        assert utcnow().tzinfo is not None

    def test_utcnow_naive_na_pas_de_timezone(self):
        assert utcnow_naive().tzinfo is None

    def test_les_deux_renvoient_un_instant_proche(self):
        ecart = abs(utcnow().replace(tzinfo=None) - utcnow_naive())
        assert ecart < datetime.timedelta(seconds=5)
