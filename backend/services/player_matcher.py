"""
PlayerMatcher service for fuzzy matching and player key generation.

Handles player name normalization, composite key generation, fuzzy matching
with rapidfuzz, and alias resolution.
"""

import logging
import re
from typing import Optional

from rapidfuzz import fuzz, process
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class PlayerMatcher:
    """Service for player matching, key generation, and alias resolution."""

    # Fuzzy matching threshold (85% as per spec)
    DEFAULT_THRESHOLD = 0.85

    def __init__(self, session: Optional[Session] = None):
        """
        Initialize PlayerMatcher.

        Args:
            session: SQLAlchemy Session for database queries (optional)
        """
        self.session = session
        self.threshold = self.DEFAULT_THRESHOLD

    def normalize_player_name(self, name: str) -> str:
        """
        Normalize player name for composite key generation.

        Steps:
        1. Remove suffixes: Jr., Sr., III, II, IV
        2. Remove prefixes: D', O'
        3. Remove all punctuation: apostrophes, periods, hyphens, commas
        4. Convert to lowercase
        5. Replace spaces with underscores
        6. Remove multiple underscores
        7. Strip leading/trailing underscores

        Examples:
        - "D'Andre Swift Jr." → "dandre_swift"
        - "A.J. Brown" → "aj_brown"
        - "Christian McCaffrey" → "christian_mccaffrey"
        - "Odell Beckham Jr." → "odell_beckham"

        Args:
            name: Player name to normalize

        Returns:
            Normalized name suitable for composite key
        """
        # Remove suffixes: Jr., Sr., III, II, IV
        suffixes = r"\s+(Jr\.?|Sr\.?|III|II|IV)$"
        name = re.sub(suffixes, "", name, flags=re.IGNORECASE)

        # Remove prefixes: D', O'
        prefixes = r"^(D'|O')"
        name = re.sub(prefixes, "", name, flags=re.IGNORECASE)

        # Remove all punctuation: apostrophes, periods, hyphens, commas
        name = re.sub(r"['\.\-,]", "", name)

        # Convert to lowercase
        name = name.lower()

        # Replace spaces with underscores
        name = name.replace(" ", "_")

        # Remove multiple underscores
        name = re.sub(r"_+", "_", name)

        # Strip leading/trailing underscores
        name = name.strip("_")

        return name

    def generate_player_key(self, name: str, team: str, position: str) -> str:
        """
        Generate composite player key.

        Format: {normalized_name}_{team}_{position}

        Example: "christian_mccaffrey_SF_RB"

        Args:
            name: Player name
            team: Player team (e.g., "SF", "LAR")
            position: Player position (e.g., "QB", "RB")

        Returns:
            Composite player key
        """
        normalized_name = self.normalize_player_name(name)
        return f"{normalized_name}_{team}_{position}"

    def fuzzy_match(
        self,
        imported_name: str,
        team: str,
        position: str,
        existing_players: list[dict],
        threshold: Optional[float] = None,
    ) -> tuple[Optional[str], float]:
        """
        Fuzzy match imported player against existing players.

        Filters candidates by team and position (exact match), then performs
        fuzzy matching against filtered candidates' names.

        Returns:
        - (player_key, similarity_score) if match found above threshold
        - (None, similarity_score) if best match below threshold

        Args:
            imported_name: Name from imported file
            team: Team abbreviation (used for exact filtering)
            position: Position (used for exact filtering)
            existing_players: List of existing player dicts with keys:
                            'name', 'player_key', 'team', 'position'
            threshold: Similarity threshold (default 0.85)

        Returns:
            Tuple of (player_key or None, similarity_score)
        """
        if threshold is None:
            threshold = self.threshold

        # Filter existing players by team and position (exact match)
        candidates = [
            p
            for p in existing_players
            if p.get("team") == team and p.get("position") == position
        ]

        if not candidates:
            return (None, 0.0)

        # Extract candidate names
        candidate_names = [p["name"] for p in candidates]

        # Fuzzy match against candidate names using rapidfuzz
        try:
            result = process.extractOne(imported_name, candidate_names, scorer=fuzz.ratio)

            if result is None:
                return (None, 0.0)

            best_match_name, score, _ = result
            similarity = score / 100.0  # Convert to 0-1 range

            if similarity >= threshold:
                # Find player_key for best match
                player = next(
                    (p for p in candidates if p["name"] == best_match_name), None
                )
                if player:
                    return (player["player_key"], similarity)

            return (None, similarity)

        except Exception as e:
            logger.error(f"Fuzzy matching failed for {imported_name}: {str(e)}")
            return (None, 0.0)

    def resolve_alias(self, alias_name: str) -> Optional[str]:
        """
        Resolve player alias to canonical player key using player_aliases table.

        Checks if the given name exists as an alias in the database and returns
        the canonical player key if found.

        Args:
            alias_name: The alias name to resolve

        Returns:
            Canonical player_key if alias exists, None otherwise
        """
        if self.session is None:
            return None

        try:
            # Query player_aliases table
            from sqlalchemy import select

            # Import here to avoid circular imports
            # This will be implemented when models are available
            # For now, return None as placeholder
            logger.debug(f"Resolving alias: {alias_name}")
            return None

        except Exception as e:
            logger.error(f"Alias resolution failed for {alias_name}: {str(e)}")
            return None
