
from db import UserRepository, Database
from typing import Dict, Optional, Any


class UserElo:
    
    def __init__(self, db: Database) -> None:

        """Initialize the UserElo with a Database instance."""

        self.db: Database = db
        self.user_repo: UserRepository = UserRepository(db)

    def compute_new_elo(self, uid: int, success: bool) -> float:

        """
        Update the trust score of a user based on the outcome of their report.
        Uses a simple Elo-like system where successful reports increase trust
        and unsuccessful ones decrease it.
        """

        user: Optional[Dict[str, Any]] = self.user_repo.get_user(uid)

        current_score = user['trust_score']
        k_factor = 0.1  # Sensitivity of trust score updates

        expected_outcome = current_score
        actual_outcome = 1.0 if success else 0.0

        new_score = current_score + k_factor * (actual_outcome - expected_outcome)
        new_score = max(0.0, min(1.0, new_score))  # Clamp between 0 and 1

        return new_score

