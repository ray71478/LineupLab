#!/bin/bash
# Quick diagnostic script to check lineup optimizer data

echo "======================================"
echo "LINEUP OPTIMIZER DATA CHECK"
echo "======================================"
echo ""

WEEK_ID=9

echo "1. Checking Vegas Lines data..."
python3 -c "
import sys
sys.path.insert(0, 'backend')
from database import get_db_url
from sqlalchemy import create_engine, text

engine = create_engine(get_db_url())
with engine.connect() as conn:
    result = conn.execute(text('SELECT COUNT(*) as total, COUNT(opponent) as with_opp FROM vegas_lines WHERE week_id = $WEEK_ID'))
    row = result.fetchone()
    print(f'  Total teams: {row[0]}')
    print(f'  With opponent: {row[1]}')
    if row[0] != row[1]:
        print(f'  ⚠️  WARNING: {row[0] - row[1]} teams missing opponent data!')
" || echo "  ✗ Error checking vegas lines"

echo ""
echo "2. Checking player data for Week $WEEK_ID..."
python3 -c "
import sys
sys.path.insert(0, 'backend')
from database import get_db_url
from sqlalchemy import create_engine, text

engine = create_engine(get_db_url())
with engine.connect() as conn:
    # Check for data issues
    result = conn.execute(text('''
        SELECT
            position,
            COUNT(*) as total,
            COUNT(CASE WHEN salary IS NULL THEN 1 END) as null_salary,
            COUNT(CASE WHEN salary = 0 THEN 1 END) as zero_salary,
            MIN(salary) as min_salary,
            MAX(salary) as max_salary
        FROM player_pool
        WHERE week_id = $WEEK_ID
        AND is_active = TRUE
        GROUP BY position
        ORDER BY position
    '''))

    print('  Position | Total | Issues | Salary Range')
    print('  ---------|-------|--------|-------------')
    issues_found = False
    for row in result:
        pos, total, null_sal, zero_sal, min_sal, max_sal = row
        issues = null_sal + zero_sal
        issue_str = f'{issues} issues' if issues > 0 else 'OK'
        if issues > 0:
            issues_found = True
            issue_str = f'⚠️  {issue_str}'
        print(f'  {pos:8} | {total:5} | {issue_str:10} | \${min_sal or 0} - \${max_sal or 0}')

    if not issues_found:
        print('  ✓ No salary issues found')
" || echo "  ✗ Error checking player data"

echo ""
echo "3. To see verbose solver output:"
echo "   - Changes have been made to enable verbose logging"
echo "   - Restart backend: pkill -f uvicorn && cd backend && ./start.sh"
echo "   - Try generating 1 lineup in the UI"
echo "   - Check backend/logs/*.log for detailed CBC solver output"
echo "   - The solver will tell you EXACTLY which constraint is failing"
echo ""
