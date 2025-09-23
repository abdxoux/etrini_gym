# /pages_logic/auth_service.py  (to implement later)
class AuthService:
    def ensure_seed_admin(self) -> None:
        """Ensure a user 'admin' with password 'admin' and role 'Admin' exists."""

    def verify(self, username: str, password: str) -> dict | None:
        """Return {'username', 'display', 'role'} on success, else None."""

    def list_users(self) -> list[dict]:
        """Return [{'id','username','display','role','created_at','disabled'} ...]."""

    def create_user(self, username: str, password: str, role: str, display: str | None = None) -> dict:
        """Create user, return user dict."""

    def update_user_role(self, user_id: int, role: str) -> None: ...

    def reset_password(self, user_id: int, new_password: str) -> None: ...

    def delete_user(self, user_id: int) -> None:
        """Allow deleting 'admin' only if there is at least one other Admin remaining."""
