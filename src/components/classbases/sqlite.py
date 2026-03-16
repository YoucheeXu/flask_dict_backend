#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os
import sqlite3
import threading
from collections.abc import Sequence, Mapping, Generator

# Preserve original type alias (use object instead of Any)
SQLParameters = Sequence[object] | Mapping[str, object] | None

# Thread-local storage: Each thread gets its OWN connection/cursor
_local = threading.local()

class SQLite:
    """ Thread-safe SQLite3 wrapper.

    Key changes for thread safety:
    1. Thread-local connections/cursors (no sharing across threads)
    2. Fresh connection per thread (never reused across threads)
    3. Strict cleanup of thread-local resources
    """
    def __init__(self):
        # No shared connection/cursor on instance (thread-local only)
        self._sqlfile: str | None = None  # Native optional type (replace Optional[str])
        self._timeout: float = 5.0  # 5s timeout for locked DB (prevents OperationalError)

    # --------------------------
    # Thread-Local Resource Helpers (Private)
    # --------------------------
    def _get_thread_conn(self) -> sqlite3.Connection:
        """ Get/create thread-local connection."""
        if not hasattr(_local, 'conn') or _local.conn is None:
            if not self._sqlfile:
                raise RuntimeError("Call open() first to initialize database!")

            # Create NEW connection for this thread (strict thread safety)
            _local.conn = sqlite3.connect(
                self._sqlfile,
                check_same_thread=True,  # Enforce SQLite's thread rule
                timeout=self._timeout,
                detect_types=sqlite3.PARSE_DECLTYPES
            )
            # Enable foreign keys (best practice)
            _ = _local.conn.execute("PRAGMA foreign_keys = ON")

        return _local.conn

    def _get_thread_cursor(self) -> sqlite3.Cursor:
        """ Get/create thread-local cursor (bound to thread's connection)."""
        conn = self._get_thread_conn()
        if not hasattr(_local, 'cur') or _local.cur is None:
            _local.cur = conn.cursor()
        return _local.cur

    def _cleanup_thread_resources(self) -> None:
        """ Close thread-local cursor/connection (safe cleanup)."""
        if hasattr(_local, 'cur') and _local.cur:
            try:
                _local.cur.close()
            except sqlite3.Error:
                pass
            _local.cur = None

        if hasattr(_local, 'conn') and _local.conn:
            try:
                _local.conn.close()
            except sqlite3.Error:
                pass
            _local.conn = None

    def open(self, sqlfile: str) -> tuple[int, str]:  # Native tuple type (replace Tuple[int, str])
        """ Open database (stores path, creates thread-local connection on first use)."""
        if not os.path.isfile(sqlfile):
            return -1, f"{sqlfile} doesn't exist!"

        # Store file path (connection created per thread via _get_thread_conn)
        self._sqlfile = sqlfile

        # Test connection for this thread (verify file is accessible)
        try:
            _ = self._get_thread_conn()
            return 1, f"{sqlfile} is OK to open!"
        except sqlite3.Error as e:
            return -1, f"Failed to open {sqlfile}: {str(e)}"

    def execute1(self, sql: str, params: SQLParameters = None) -> bool:
        """ Execute SQL with **automatic commit** (for write operations: INSERT/UPDATE/DELETE/CREATE).

        Ideal for single, atomic write operations that need immediate persistence. Supports
        parameterized queries to prevent SQL injection.

        Args:
            sql: Valid SQLite SQL statement (DDL/DML).
            params: Optional parameter for parameterized queries, defaulting to None:
                - Sequence types (e.g., tuple, list): Matched with "?" placeholders by position
                - Dictionary types (e.g., dict): Matched with ":key" placeholders by key name
                - None: Indicates a query without parameters

        Returns:
            bool: True if the SQL execution succeeds, False if it fails (e.g., invalid syntax).

        Raises:
            RuntimeError: If called before open() (no active database connection).
            sqlite3.Error: For SQL execution errors (e.g., syntax error, constraint violation)
                (no exception handling in this method).

        Example:
            >>> db.open(":memory:")
            >>> db.execute1("CREATE TABLE users (id INT, name TEXT)")  # True
            >>> db.execute1("INSERT INTO users VALUES (?, ?)", (1, "Alice"))  # True
            >>> db.execute1("INSERT INTO users VALUES (:id, :name)", {"id": 2, "name": "Bob"})  # True
        """
        if not self._sqlfile:
            raise RuntimeError("Call open() first to initialize connection!")

        conn = self._get_thread_conn()
        cursor: sqlite3.Cursor | None = None  # Native optional type (replace Optional[sqlite3.Cursor])

        try:
            cursor = conn.cursor()
            # Execute with parameters (prevent SQL injection)
            _ = cursor.execute(sql, params if params is not None else ())
            conn.commit()  # Auto-commit for write operations
            return cursor.rowcount == 1  # Match original return logic

        except sqlite3.Error as e:
            if conn:
                conn.rollback()  # Rollback on error
            raise RuntimeError(f"Failed to execute {sql} with {params}") from e

        finally:
            if cursor:
                cursor.close()  # Clean up cursor (critical)

    def excute(self, command: str) -> None:
        """ execute wihtout commit"""
        if not self._sqlfile:
            raise RuntimeError("Call open() first to initialize connection!")

        cursor = self._get_thread_cursor()
        _ = cursor.execute(command)  # No commit (call commit() manually)

    def commit(self) -> None:
        """ Commit transaction"""
        conn = self._get_thread_conn()
        conn.commit()

    def get(self, query: str) -> tuple[object, ...] | None:  # Use object instead of Any + native optional
        """ Get first row of query result"""
        if not self._sqlfile:
            raise RuntimeError("Call open() first to initialize connection!")

        cursor = self._get_thread_cursor()
        _ = cursor.execute(query)
        return cursor.fetchone()

    def each(self, query: str, params: SQLParameters = None) -> Generator[tuple[object, ...], None, None]:
        """ Return a generator to iterate over **all rows** of a query result (lazy evaluation).

        Efficient for large result sets (does not load all rows into memory at once).
        Each iteration returns a row as a tuple.

        Args:
            query: the query statement
            params: Optional parameter for parameterized queries, defaulting to None:
                - Sequence types (e.g., tuple, list): Matched with "?" placeholders by position
                - Dictionary types (e.g., dict): Matched with ":key" placeholders by key name
                - None: Indicates a query without parameters

        Yields:
            tuple[object, ...]: Each row of the query result as a tuple.

        Raises:
            RuntimeError: If called before open() (no active database connection).
            sqlite3.Error: For invalid query syntax or execution errors.

        Example:
            >>> db.open(":memory:")
            >>> db.execute1("INSERT INTO users VALUES (1, 'Alice'), (2, 'Bob')")
            >>> for row in db.each("SELECT * FROM users ORDER BY id"):
            ...     print(row)
            (1, 'Alice')
            (2, 'Bob')
        """
        if not self._sqlfile:
            raise RuntimeError("Call open() first to initialize connection!")

        conn = self._get_thread_conn()
        cursor: sqlite3.Cursor | None = None  # Native optional type (replace Optional[sqlite3.Cursor])

        try:
            cursor = conn.cursor()
            # Execute query with parameters
            _ = cursor.execute(query, params if params is not None else ())

            # Yield rows one at a time (lazy evaluation)
            yield from cursor

        finally:
            if cursor:
                cursor.close()  # Clean up cursor when generator is exhausted

    def close(self) -> bool:
        """ Close database (clean up ALL thread-local resources) """
        self._cleanup_thread_resources()
        self._sqlfile = None  # Reset file path
        return True

    def __del__(self):
        """ Destructor - ensure thread-local resources are cleaned up."""
        _ = self.close()

    def enable_wal(self) -> bool:
        """ Enable Write-Ahead Logging (improves concurrency for write-heavy workloads)."""
        if not self._sqlfile:
            raise RuntimeError("Call open() first!")

        try:
            conn = self._get_thread_conn()
            _ = conn.execute("PRAGMA journal_mode = WAL")
            conn.commit()
            return True
        except sqlite3.Error as e:
            raise RuntimeError(f"Failed to enable WAL: {str(e)}") from e
