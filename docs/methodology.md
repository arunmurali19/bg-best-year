# Methodology: Board Game Best Year Tournament

## Data Source

The tournament uses BoardGameGeek (BGG) rankings data from `data/bgg_games.csv`, which contains all ranked games on BGG. The **top 2000 ranked games** are used for scoring years, while the voting UI displays only the top 1000 games per year.

## Year Scoring

Each year receives a weighted score based on the ranks of its games in the top 2000. Higher-ranked games contribute more points:

| Rank Range  | Points Per Game |
|------------|----------------|
| 1 - 20     | 10             |
| 21 - 100   | 6              |
| 101 - 250  | 5              |
| 251 - 500  | 4              |
| 501 - 750  | 3              |
| 751 - 1000 | 2              |
| 1001 - 2000| 1              |

This tiered system ensures that years with truly elite games (top 20) are weighted heavily, while the 1001-2000 range still contributes a baseline point per game. A single top-20 game is worth ten bottom-tier games.

The full year-by-year breakdown is available in `data/internal_analysis.csv`.

## Year Selection

The top 32 years by total score are selected for the tournament. Years are then assigned seeds 1 through 32 based on their score ranking (1 = highest score).

## Bracket Seeding

The bracket uses **tennis-style seeding** to ensure the strongest years meet as late as possible in the tournament:

- Seeds 1 and 2 are placed on opposite sides of the bracket (can only meet in the Final)
- Seeds 1-4 can only meet in the Semifinals
- Seeds 1-8 can only meet in the Quarterfinals

Round 1 matchups follow the standard format: 1v32, 16v17, 9v24, 8v25, 5v28, 12v21, 13v20, 4v29, 3v30, 14v19, 11v22, 6v27, 7v26, 10v23, 15v18, 2v31.

Seeds are stored internally for bracket construction but are **never displayed** to voters, to avoid biasing their decisions.

## Tournament Format

- **Round of 32**: 16 matchups
- **Round of 16**: 8 matchups
- **Quarterfinals**: 4 matchups
- **Semifinals**: 2 matchups
- **Final**: 1 matchup

Each round is opened for voting by an admin. When a round closes, the year with more votes advances. In case of a tie, the higher-seeded year advances (this is the only place seeds have a visible effect, and it is rare).

## Anti-Fraud Measures

- Each browser receives a unique voter UUID via cookie
- A database constraint prevents any voter from voting twice on the same matchup
- IP addresses are logged for admin review

## Modularity

The system is designed to accommodate more than 32 years. If `TOTAL_YEARS` is increased (e.g., to 40), the bracket size remains at 32 (a power of 2), and the lowest-seeded years play "play-in" rounds before joining the main bracket. The top seeds receive byes past the play-in round.
