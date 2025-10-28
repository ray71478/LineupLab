# Data Import System - File Structures

**Last Updated:** October 27, 2025

## File Structure Analysis

### 1. LineStar File

**File Name Pattern:** `LineStar_Football_WK{X}.xlsx` (where X = week number)

**Sheet Name:** Variable (e.g., `LineStar_Football_Main_9613`)
- **Strategy:** Use first sheet (index 0) since there's only one sheet

**Columns (28 total):**
- `LineStarId` - Unique identifier
- `Name` - Player name
- `Position` - QB, RB, WR, TE, DST
- `Team` - Team abbreviation
- `Salary` - DraftKings salary (integer)
- `Projected` - Projected FPTS (float)
- `Scored` - Actual scored points (may be null for future weeks)
- `IsOverridden` - Boolean flag
- `OppRank` - Opponent defensive rank
- `OppRankTotal` - Total opponent rank
- `Ceiling` - Ceiling projection (float)
- `Floor` - Floor projection (float)
- `StartingStatus` - Starting status indicator
- `Consistency` - Consistency score
- `ProjOwn` - Projected ownership % (float)
- `Consensus` - Consensus projection
- `Leverage` - Leverage score
- `Safety` - Safety score
- `AlertScore` - Alert score
- `SIC` - SIC metric
- `PPG` - Points per game
- `VersusStr` - Versus string
- `DFS_ID` - DFS platform ID
- `Vegas` - Vegas line
- `VegasML` - Vegas moneyline
- `VegasTotals` - Vegas totals
- `VegasImplied` - Vegas implied total
- `Depth` - Depth chart position

**Row Count:** ~505 players

**Required Columns for Import:**
- `Name`, `Position`, `Team`, `Salary`, `Projected`, `Ceiling`, `Floor`, `ProjOwn`

---

### 2. DraftKings File

**File Name Pattern:** `DKSalaries Week {X}.xlsx` (where X = week number)

**Sheet Names:** `FE`, `ETR`, `ITT`

#### Sheet: FE (FantasyPros Expert Consensus)

**Header Row:** Row 2 (index 1) - Row 1 contains some numeric values (ignore)

**Columns:**
- `ID` - DraftKings player ID
- `Pos` - Position (QB, RB, WR, TE, DST)
- `Name` - Player name
- `T` - Team abbreviation
- `S` - Salary (integer)
- `Game Info` - Game matchup and time
- `GID` - Game ID
- `Own` - Projected ownership % (float, 0-1 format, e.g., 0.112 = 11.2%)
- `Flr` - Floor projection (float)
- `Proj` - Projected FPTS (float)
- `3.5X` - 3.5x value indicator
- `Ceil` - Ceiling projection (float)
- `ITT` - Implied team total (float)
- `Pl` - Unknown field
- `Notes` - Player notes

**Row Count:** ~174 players

**Required Columns for Import:**
- `Name`, `Pos`, `T`, `S`, `Own`, `Flr`, `Proj`, `Ceil`, `ITT`

#### Sheet: ETR (Establish The Run)

**Header Row:** Row 1 (index 0)

**Columns:**
- `id` - Player ID
- `Player` - Player name
- `DK Pos` - Position
- `Team` - Team abbreviation
- `Opp` - Opponent team
- `DK Salary` - Salary (integer)
- `DK Floor` - Floor projection (float)
- `DK Proj` - Projected FPTS (float)
- `DK Ceiling` - Ceiling projection (float)
- `DK Value` - Value score
- `Large Field` - Projected ownership % (float, 0-1 format)

**Row Count:** ~267 players

**Required Columns for Import:**
- `Player`, `DK Pos`, `Team`, `DK Salary`, `DK Floor`, `DK Proj`, `DK Ceiling`, `Large Field`

#### Sheet: ITT (Implied Team Totals)

**Header Row:** Row 1 (index 0)

**Columns:**
- `Tm Ab` - Team abbreviation
- `Rk` - Rank
- `Team` - Full team name
- `ITT` - Implied team total (float)
- `Spread` - Point spread (float)
- `OU` - Over/under (float)
- `Opp` - Opponent abbreviation

**Row Count:** 32 teams (all NFL teams)

**Required Columns for Import:**
- `Tm Ab`, `ITT`, `Spread`, `OU`, `Opp`

---

### 3. Comprehensive Stats File

**File Name Pattern:** `ComprehensiveStats_throughWeek{X}.xlsx` (where X = last completed week)

**Sheet Names:** Multiple sheets, primary focus on `Points` sheet

#### Sheet: Points (Primary Historical Data)

**Columns (30 total):**
- `id` - Player ID
- `Player` - Player name
- `Tm` - Team abbreviation
- `Pos` - Position
- `Wk` - Week number (integer)
- `Opp` - Opponent team
- `Snaps` - Total snaps (integer)
- `Snp %` - Snap percentage (float, 0-1 format)
- `P_yds` - Passing yards
- `P_TD` - Passing touchdowns
- `Int` - Interceptions
- `Ratt` - Rush attempts
- `Rsh_yds` - Rushing yards
- `Rsh_td` - Rushing touchdowns
- `Rtes` - Unknown field
- `CTGT` - Catchable targets
- `CTGT%` - Catchable target percentage
- `TPRR` - Targets per route run
- `Rec` - Receptions
- `Rc_yds` - Receiving yards
- `Rc_td` - Receiving touchdowns
- `Tot TD` - Total touchdowns
- `Touch` - Total touches
- `S Yds Q` - Unknown field
- `S Yds S` - Unknown field
- `DK Pts` - Actual DraftKings points scored (float)
- `Sal` - Salary that week
- `Val` - Value (DK Pts / Salary * 1000)
- `Slate` - Slate type
- `ITT` - Implied team total

**Row Count:** ~2,690 player-week records (across all weeks)

**Required Columns for Import:**
- `Player`, `Tm`, `Pos`, `Wk`, `Opp`, `Snaps`, `Snp %`, `Ratt`, `Rsh_yds`, `Rsh_td`, `CTGT`, `CTGT%`, `Rec`, `Rc_yds`, `Rc_td`, `Tot TD`, `Touch`, `DK Pts`, `Sal`

#### Sheet: Chosen (Season Aggregates)

**Columns:**
- `player`, `Name`, `team`, `pos`, `gp`, `snaps`, `snaps_per_gp`, `snap_pct`, `rush_per_snap`, `rush_share`, `tgt_per_snap`, `tgt_share`, `touch_per_snap`, `util_per_snap`, `fpts_ppr`, `fpts_ppr_per_snap`

**Row Count:** ~525 players

**Use Case:** Season-long aggregates (optional for MVP, may use in Phase 2)

#### Sheet: Milly (Ownership History)

**Columns:**
- `Player`, `Pos`, `Week`, `%Drafted`, `FPTS`, `Salary`, `Value`, `Pts Rk`, `ETR Flr`, `ETR Proj`, `ETR Ceil`, `ETR Own%`, `Diff in Own`

**Row Count:** ~1,696 player-week records

**Use Case:** Historical ownership data (optional for MVP, may use in Phase 2)

---

## Import Strategy

### LineStar Import
1. Read first sheet (index 0)
2. Map columns: `Name` → `name`, `Position` → `position`, `Team` → `team`, `Salary` → `salary`, `Projected` → `projection`, `Ceiling` → `ceiling`, `Floor` → `floor`, `ProjOwn` → `ownership`
3. Generate `player_key` = `normalize_name(Name)_Team_Position`
4. Set `source` = "LineStar"
5. Bulk insert into `player_pools` table

### DraftKings Import
1. **Prompt user:** "Which projections: FE or ETR?" and "Which ownership: FE or ETR?"
2. Read selected projection sheet (FE or ETR)
   - **FE:** Skip row 1, use row 2 as header
   - **ETR:** Use row 1 as header
3. Read ITT sheet (always import)
4. Map columns based on selected sheet
5. Generate `player_key` = `normalize_name(Name)_Team_Position`
6. Set `source` = "DraftKings"
7. **Delete all existing players for this week** (overwrite behavior)
8. Bulk insert into `player_pools` table
9. Insert ITT data into `vegas_lines` table

### Comprehensive Stats Import
1. Read `Points` sheet
2. Map columns to `historical_stats` table
3. Generate `player_key` = `normalize_name(Player)_Tm_Pos`
4. **Delete all existing historical stats** (full replace)
5. Bulk insert into `historical_stats` table
6. **Automated backup:** Before delete, create backup of `historical_stats` table (keep 1 previous version)

---

## Column Mapping Reference

### LineStar → player_pools
```python
{
    "Name": "name",
    "Position": "position",
    "Team": "team",
    "Salary": "salary",
    "Projected": "projection",
    "Ceiling": "ceiling",
    "Floor": "floor",
    "ProjOwn": "ownership",  # Convert to 0-1 if needed
}
```

### DraftKings FE → player_pools
```python
{
    "Name": "name",
    "Pos": "position",
    "T": "team",
    "S": "salary",
    "Proj": "projection",
    "Ceil": "ceiling",
    "Flr": "floor",
    "Own": "ownership",  # Already in 0-1 format
}
```

### DraftKings ETR → player_pools
```python
{
    "Player": "name",
    "DK Pos": "position",
    "Team": "team",
    "DK Salary": "salary",
    "DK Proj": "projection",
    "DK Ceiling": "ceiling",
    "DK Floor": "floor",
    "Large Field": "ownership",  # Already in 0-1 format
}
```

### DraftKings ITT → vegas_lines
```python
{
    "Tm Ab": "team",
    "ITT": "implied_team_total",
    "Spread": "spread",
    "OU": "over_under",
    "Opp": "opponent",
}
```

### Comprehensive Stats Points → historical_stats
```python
{
    "Player": "player_name",
    "Tm": "team",
    "Pos": "position",
    "Wk": "week",
    "Opp": "opponent",
    "Snaps": "snaps",
    "Snp %": "snap_pct",
    "Ratt": "rush_attempts",
    "Rsh_yds": "rush_yards",
    "Rsh_td": "rush_tds",
    "CTGT": "targets",
    "CTGT%": "target_share",
    "Rec": "receptions",
    "Rc_yds": "rec_yards",
    "Rc_td": "rec_tds",
    "Tot TD": "total_tds",
    "Touch": "touches",
    "DK Pts": "actual_points",
    "Sal": "salary",
}
```

