#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os
from collections.abc import Sequence, Mapping
import sqlite3
# from typing import Any
from collections.abc import Generator


# Sequence/dict for parameterized queries (None = no parameters)
SQLParameters = Sequence[object] | Mapping[str, object] | None

class SQLite:
    def __init__(self):
        self._conn: sqlite3.Connection
        self._cur: sqlite3.Cursor

    # def Open(self, path: str) -> str:
        # _this = this;
        # return Promise((resolve, reject) => {
            # _this.db = sqlite3.Database(path,
                # (err: Error | null) => {
                    # if (err) {
                        # console.error("Open error: " + err.message);
                        # reject("Open error: " + err.message);
                    # }
                    # else {
                        # print(path + " opened");
                        # resolve(path + " opened");
                    # }
                # }
            # )
        # })
    # }
    def open(self, sqlfile: str) -> tuple[int, str]:
        if not os.path.isfile(sqlfile):
            return -1, f"{sqlfile} doesn't exit!"

        self._conn = sqlite3.connect(sqlfile)
        if self._conn:
            self._cur = self._conn.cursor()
        else:
            return -1, f"fail to open {sqlfile}"

        return 1, sqlfile + "is OK to open!"

    # any query: insert/delete/update
    def excute1(self, command: str) -> bool:
        ret = self._cur.execute(command)
        if not ret:
            return False

        self._conn.commit()
        return True

    def execute1(self, sql: str, params: SQLParameters = None):
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
        if not self._conn:
            raise RuntimeError("Call open() first to initialize connection!")

        try:
            # Create cursor, execute query, commit immediately
            cursor = self._conn.cursor()
            # Bind parameters (match column order)
            _ = cursor.execute(sql, params if params is not None else ())
            self._conn.commit()  # Auto-commit for immediate persistence
            cursor.close()
            # return bool(ret)
            # Check if row was inserted (cursor.rowcount = 1 if inserted, 0 if skipped)
            return cursor.rowcount == 1

        except sqlite3.Error as e:
            # Rollback transaction on error to avoid partial changes
            if self._conn:
                self._conn.rollback()
            raise RuntimeError(
                f"Failed to execute {sql} with {params}"
            ) from e

    def excute(self, command: str):
        _ = self._cur.execute(command)

    def commit(self):
        self._conn.commit()

    def get(self, query: str):
        # first row read
        _ = self._cur.execute(query)
        records = self._cur.fetchone()
        return records

    def each(self, query: str, params: SQLParameters = None) -> Generator[object, object, object]:
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
        if not self._conn:
            raise RuntimeError("Call open() first to initialize connection!")

        # Create cursor, execute query, yield rows one at a time
        cursor = self._conn.cursor()
        yield from cursor.execute(query, params if params is not None else ())
        cursor.close()  # Clean up cursor after generator is exhausted

    def close(self) -> bool:
        if self._cur:
            self._cur.close()
        if self._conn:
            self._conn.close()
        return True
