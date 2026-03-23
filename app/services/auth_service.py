from app.db.models.user import User


def has_permission(user: User, permission_name: str) -> bool:
    for role in user.roles:
        for perm in role.permissions:
            if perm.name == permission_name:
                return True
    return False
