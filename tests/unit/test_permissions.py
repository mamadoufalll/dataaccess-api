import pytest

from app.core.permissions import (
    can_publish,
    can_reject,
    is_admin,
    is_data_steward,
    is_owner,
)
from app.models.user import User, UserRole


def make_user(role: UserRole, user_id: int = 1) -> User:
    utilisateur = User()
    utilisateur.id = user_id
    utilisateur.role = role
    return utilisateur


class TestIsDataSteward:
    def test_accepte_un_data_steward(self):
        assert is_data_steward(make_user(UserRole.DATA_STEWARD)) is True

    @pytest.mark.parametrize(
        "role", [UserRole.PRODUCER, UserRole.REQUESTER, UserRole.ADMIN]
    )
    def test_refuse_les_autres_roles(self, role):
        assert is_data_steward(make_user(role)) is False


class TestIsAdmin:
    def test_accepte_un_admin(self):
        assert is_admin(make_user(UserRole.ADMIN)) is True

    @pytest.mark.parametrize(
        "role", [UserRole.PRODUCER, UserRole.REQUESTER, UserRole.DATA_STEWARD]
    )
    def test_refuse_les_autres_roles(self, role):
        assert is_admin(make_user(role)) is False


class TestCanPublish:
    @pytest.mark.parametrize("role", [UserRole.DATA_STEWARD, UserRole.ADMIN])
    def test_autorise_steward_et_admin(self, role):
        assert can_publish(make_user(role)) is True

    def test_un_producteur_ne_peut_pas_publier(self):
        """Invariant du sujet : la publication passe par une validation."""
        assert can_publish(make_user(UserRole.PRODUCER)) is False

    def test_un_demandeur_ne_peut_pas_publier(self):
        assert can_publish(make_user(UserRole.REQUESTER)) is False


class TestCanReject:
    @pytest.mark.parametrize("role", [UserRole.DATA_STEWARD, UserRole.ADMIN])
    def test_autorise_steward_et_admin(self, role):
        assert can_reject(make_user(role)) is True

    @pytest.mark.parametrize("role", [UserRole.PRODUCER, UserRole.REQUESTER])
    def test_refuse_producteur_et_demandeur(self, role):
        assert can_reject(make_user(role)) is False


class TestIsOwner:
    def test_accepte_le_proprietaire(self):
        assert is_owner(make_user(UserRole.PRODUCER, user_id=7), 7) is True

    def test_refuse_un_autre_utilisateur(self):
        assert is_owner(make_user(UserRole.PRODUCER, user_id=7), 8) is False
