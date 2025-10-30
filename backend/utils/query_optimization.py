"""
Database Query Optimization Utilities

Performance optimization strategies:
- Query result caching using Redis (if available)
- Database query pagination
- Eager loading with joinedload
- Query plan analysis with EXPLAIN
- Index usage verification
- N+1 query prevention

Target: All queries <100ms
"""

import logging
import time
from functools import wraps
from typing import Any, Callable, Optional, Dict, List, TypeVar
from datetime import datetime, timedelta

from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

T = TypeVar('T')

# Simple in-memory cache (replace with Redis in production)
_query_cache: Dict[str, tuple[Any, float]] = {}
CACHE_TTL = 300  # 5 minutes


def clear_query_cache():
    """Clear the query cache."""
    global _query_cache
    _query_cache.clear()


def query_cache(ttl: int = CACHE_TTL):
    """
    Decorator to cache query results.

    Args:
        ttl: Time to live in seconds (default: 5 minutes)

    Usage:
        @query_cache(ttl=300)
        def get_weeks_by_year(session, year):
            return session.query(Week).filter(Week.season == year).all()
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            # Create cache key from function name and arguments
            cache_key = f"{func.__name__}:{str(args)}{str(kwargs)}"

            # Check cache
            if cache_key in _query_cache:
                result, timestamp = _query_cache[cache_key]
                if datetime.now() - timestamp < timedelta(seconds=ttl):
                    logger.debug(f"Cache HIT: {func.__name__}")
                    return result

            # Execute function and cache result
            logger.debug(f"Cache MISS: {func.__name__}")
            result = func(*args, **kwargs)
            _query_cache[cache_key] = (result, datetime.now())
            return result

        return wrapper
    return decorator


def measure_query_time(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to measure query execution time.

    Logs warning if query takes longer than 100ms.

    Usage:
        @measure_query_time
        def get_weeks_by_year(session, year):
            return session.query(Week).filter(Week.season == year).all()
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> T:
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            elapsed = (time.time() - start_time) * 1000  # Convert to ms

            if elapsed > 100:
                logger.warning(
                    f"SLOW QUERY: {func.__name__} took {elapsed:.2f}ms (target: <100ms)"
                )
            else:
                logger.debug(
                    f"Query {func.__name__} took {elapsed:.2f}ms"
                )

            return result
        except SQLAlchemyError as e:
            logger.error(f"Query failed in {func.__name__}: {str(e)}")
            raise

    return wrapper


def analyze_query_plan(session: Session, query_string: str) -> Dict[str, Any]:
    """
    Analyze query execution plan using EXPLAIN.

    Args:
        session: SQLAlchemy session
        query_string: SQL query to analyze

    Returns:
        Dictionary with execution plan details

    Usage:
        plan = analyze_query_plan(
            session,
            "SELECT * FROM weeks WHERE season = 2025"
        )
        print(plan)
    """
    try:
        # PostgreSQL EXPLAIN ANALYZE
        explain_query = f"EXPLAIN ANALYZE {query_string}"
        result = session.execute(text(explain_query))
        rows = result.fetchall()

        plan = {
            'query': query_string,
            'plan': [row[0] for row in rows],
            'timestamp': datetime.now().isoformat(),
        }

        logger.info(f"Query Plan Analysis:\n{chr(10).join(plan['plan'])}")
        return plan

    except SQLAlchemyError as e:
        logger.error(f"Failed to analyze query plan: {str(e)}")
        return {
            'query': query_string,
            'error': str(e),
        }


def verify_indexes_used(session: Session, table_name: str) -> List[str]:
    """
    Verify that indexes exist for a table.

    Args:
        session: SQLAlchemy session
        table_name: Table name to check

    Returns:
        List of index names

    Usage:
        indexes = verify_indexes_used(session, 'weeks')
        print(f"Indexes: {indexes}")
    """
    try:
        query = f"""
            SELECT indexname FROM pg_indexes WHERE tablename = '{table_name}'
        """
        result = session.execute(text(query))
        indexes = [row[0] for row in result.fetchall()]
        logger.info(f"Indexes for {table_name}: {indexes}")
        return indexes

    except SQLAlchemyError as e:
        logger.error(f"Failed to verify indexes: {str(e)}")
        return []


class QueryOptimizer:
    """Helper class for common query optimization patterns."""

    @staticmethod
    def paginate_query(
        session: Session,
        query_obj: Any,
        page: int = 1,
        page_size: int = 18
    ) -> tuple[List[Any], int]:
        """
        Paginate query results.

        Args:
            session: SQLAlchemy session
            query_obj: Query object to paginate
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            Tuple of (items, total_count)

        Usage:
            items, total = QueryOptimizer.paginate_query(
                session,
                session.query(Week).filter(Week.season == 2025),
                page=1,
                page_size=18
            )
        """
        # Get total count
        total_count = query_obj.count()

        # Calculate offset
        offset = (page - 1) * page_size

        # Get paginated results
        items = query_obj.offset(offset).limit(page_size).all()

        logger.debug(
            f"Paginated query: page={page}, page_size={page_size}, "
            f"total={total_count}, returned={len(items)}"
        )

        return items, total_count

    @staticmethod
    def batch_fetch(
        session: Session,
        ids: List[int],
        model_class: type,
        id_column: str = 'id',
        batch_size: int = 100
    ) -> List[Any]:
        """
        Fetch multiple records efficiently using batch queries.

        Args:
            session: SQLAlchemy session
            ids: List of IDs to fetch
            model_class: Model class to query
            id_column: Column name for IDs
            batch_size: Items per batch query

        Returns:
            List of fetched objects

        Usage:
            weeks = QueryOptimizer.batch_fetch(
                session, [1, 2, 3], Week, 'id'
            )
        """
        results = []

        for i in range(0, len(ids), batch_size):
            batch_ids = ids[i:i + batch_size]
            batch_results = session.query(model_class).filter(
                getattr(model_class, id_column).in_(batch_ids)
            ).all()
            results.extend(batch_results)

        logger.debug(
            f"Batch fetch: {len(ids)} IDs in {len(results)} results"
        )

        return results

    @staticmethod
    def eager_load_relationships(
        query_obj: Any,
        relationships: List[str]
    ) -> Any:
        """
        Eagerly load related objects to prevent N+1 queries.

        Args:
            query_obj: Query object
            relationships: List of relationship names to eagerly load

        Returns:
            Modified query object

        Usage:
            from sqlalchemy.orm import joinedload
            query = QueryOptimizer.eager_load_relationships(
                session.query(Week),
                ['metadata', 'status_overrides']
            )
        """
        for relationship in relationships:
            from sqlalchemy.orm import joinedload
            query_obj = query_obj.options(joinedload(getattr(query_obj.column_descriptions[0]['entity'], relationship)))

        return query_obj


# Performance monitoring decorator
def monitor_performance(threshold_ms: int = 100):
    """
    Monitor function performance and log warnings for slow operations.

    Args:
        threshold_ms: Performance threshold in milliseconds

    Usage:
        @monitor_performance(threshold_ms=100)
        def get_weeks(session, year):
            return session.query(Week).filter(Week.season == year).all()
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            start = time.time()
            try:
                result = func(*args, **kwargs)
                elapsed = (time.time() - start) * 1000

                if elapsed > threshold_ms:
                    logger.warning(
                        f"SLOW: {func.__name__} took {elapsed:.2f}ms "
                        f"(threshold: {threshold_ms}ms)"
                    )
                else:
                    logger.info(
                        f"{func.__name__} completed in {elapsed:.2f}ms"
                    )

                return result
            except Exception as e:
                elapsed = (time.time() - start) * 1000
                logger.error(
                    f"ERROR in {func.__name__} after {elapsed:.2f}ms: {str(e)}"
                )
                raise

        return wrapper
    return decorator
