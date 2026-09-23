## Spanish Learning App — Data Rules

- `vocab.db` contains the user's learning progress. Treat it as production data.
- Before ANY script that touches `vocab.db`, run: `cp vocab.db vocab.db.bak`
- The `next_review`, `interval`, `repetitions`, and `ease_factor` columns (both passive and active) represent weeks of learning. NEVER reset them.
- The `is_ignored` column tracks user's manual deletions. NEVER bulk-reset it.
- When adding features, ADD new columns. Never repurpose or overwrite existing columns.
- The `word` column must match the original lemmatized form from the JSON. Never prefix/suffix it.
