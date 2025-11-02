# Showdown Mode for Single-Game Contests

## Feature Description

The user wants to add support for DraftKings Showdown contests (single-game slates) while preserving the existing main slate workflow.

## Key Requirements

1. **File Import**: Import Linestar CSV files for showdown contests (different format from main slate - includes Captain designation and potentially kickers)

2. **Roster Construction**: Different from main slate
   - Single game instead of full slate
   - One Captain (typically 1.5x points)
   - Flex positions (usually 5 additional players)
   - All players from same game

3. **Preserve Existing Flow**: Do NOT change the current main slate workflow
   - Reuse existing components: Player Selection, Smart Score Engine, Lineup Generator
   - Keep all existing lineup generator constraints/switches available
   - User will control which constraints make sense for showdown manually

4. **UI Consideration**: Must not "blow up" the current UI - needs elegant integration that keeps main slate flow intact

5. **Goal**: Allow same beautiful flow (import → player selection → lineup generation) but for showdown format
