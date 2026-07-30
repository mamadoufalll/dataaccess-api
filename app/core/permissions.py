from app.models.user import User, UserRole

def is_data_steward(user: User) -> bool:
    return user.role == UserRole.DATA_STEWARD

def is_admin(user: User) -> bool:
    return user.role == UserRole.ADMIN

def can_publish(user: User) -> bool:
    return user.role in (UserRole.DATA_STEWARD, UserRole.ADMIN)

def can_reject(user: User) -> bool:
    return user.role in (UserRole.DATA_STEWARD, UserRole.ADMIN)

def is_owner(user: User, owner_id: int) -> bool:
    return user.id == owner_id
