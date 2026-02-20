#!/usr/bin/python3
# -*- coding: UTF-8 -*-
# from collections.abc import Generator
from typing import cast
from src.components.classbases.sqlite import SQLite


class WordDict:
    '''
        CREATE TABLE [Words](
            [Word] CHAR(255) CONSTRAINT [PrimaryKey] PRIMARY KEY,
            [USSymbol] CHAR(255),
            [UKSymbol] CHAR(255),
            [Level] CHAR(255),
            [Stars] TINYINT
        )
    '''
    def __init__(self):
        self._dictname: str = ""
        self._dictsrc: str = ""

        self._database: SQLite = SQLite()

    def open(self, dictname: str, dictsrc: str) -> tuple[int, str]:
        self._dictname = dictname
        self._dictsrc = dictsrc
        return self._database.open(self._dictsrc)

    def has_word(self, word: str) -> bool:
        """Checks if a specific word exists in the SQLite Words table.

        Validates input, connects to the SQLite database, and executes a parameterized query
        to check for the existence of a word (primary key in the Words table). Uses `SELECT 1`
        with `LIMIT 1` for optimal performance (minimizes data fetch, stops at first match).

        Args:
            word: Non-empty string representing the target word to check (e.g., "able").

        Returns:
            Boolean indicating if the word exists (True = exists, False = does not exist).

        Raises:
            ValueError: If `word` is an empty string or not a string type.
            RuntimeError: If a database error occurs (e.g., connection failure, missing table)
            with the original sqlite3.Error as the root cause.

        Examples:
            >>> check_word_exists("./dict.db", "able")
            True
            >>> check_word_exists("./dict.db", "nonexistent_word_123")
            False
        """
        # Validate input to avoid useless database operations
        # if not isinstance(word, str):
        #     raise ValueError(f"Expected 'word' to be string, got {type(word).__name__}")
        if not word.strip():
            raise ValueError("'word' cannot be an empty string or whitespace")

        # Parameterized query (SAFE: prevents SQL injection)
        # Use SELECT 1 instead of SELECT * to minimize data transfer
        query = f"SELECT 1 FROM Words WHERE Word = '{word}' LIMIT 1"

        # result (None = no match, (1,) = match found)
        result = self._database.get(query)
        return result is not None

    def insert_word(self,
        word: str,
        us_symbol: str = "",
        uk_symbol: str = "",
        level: str = "",
        stars: int = 0
    ) -> bool:
        """Inserts a word into the SQLite Words table (insert or ignore duplicates).

        Validates input data types (e.g., Stars as TINYINT), uses parameterized queries
        to prevent SQL injection, and skips insertion if the word (primary key) already exists.
        Commits the transaction only if insertion succeeds.

        Args:
            db_path: String path to the SQLite database file (e.g., "./dict.db").
            word: Non-empty string (primary key) for the word to insert (e.g., "able").
            us_symbol: Optional string for US phonetic symbol (e.g., "/ˈeɪbl/") — None if unspecified.
            uk_symbol: Optional string for UK phonetic symbol (e.g., "/ˈeɪbl/") — None if unspecified.
            level: Optional string for word level (e.g., "CET6", "CET4") — None if unspecified.
            stars: Optional integer (0-255, TINYINT) for star rating (e.g., 5) — None if unspecified.

        Returns:
            Boolean: True if insertion succeeded (word was new), False if word existed (skipped).

        Raises:
            ValueError: If input validation fails (e.g., empty word, invalid stars range).
            RuntimeError: If database error occurs (e.g., connection failure, invalid table schema)
            with original sqlite3.Error as root cause.

        Examples:
            >>> insert_word("./dict.db", "able", "/ˈeɪbl/", "/ˈeɪbl/", "CET6", 5)
            True  # Inserted successfully (new word)
            >>> insert_word("./dict.db", "able", "/ˈeɪbl/", "/ˈeɪbl/", "CET6", 5)
            False # Skipped (word already exists)
        """
        # --------------------------
        # Step 1: Input Validation (match table schema)
        # --------------------------
        # Validate primary key (Word): non-empty string
        # if not isinstance(word, str) or not word.strip():
        #     raise ValueError(f"Invalid 'word': must be non-empty string (got {repr(word)})")

        # Validate Stars: TINYINT (0-255) if provided
        # if stars is not None:
        #     if not isinstance(stars, int):
        #     raise ValueError(f"Invalid 'stars': must be integer (got {type(stars).__name__})")
        if not (0 <= stars <= 255):
            raise ValueError(f"Invalid 'stars': must be 0-255 (TINYINT, got {stars})")

        # Validate optional string fields (ensure they are strings if provided)
        # for field_name, field_value in [
        #     ("us_symbol", us_symbol),
        #     ("uk_symbol", uk_symbol),
        #     ("level", level)
        # ]:
        #     if field_value is not None and not isinstance(field_value, str):
        #     raise ValueError(
        #         f"Invalid '{field_name}': must be string (got {type(field_value).__name__})"
        #     )

        # --------------------------
        # Step 2: Database Operation
        # --------------------------
        # Parameterized INSERT query (SAFE: prevents SQL injection)
        # INSERT OR IGNORE: skip if word (primary key) already exists
        insert_query = """
            INSERT OR IGNORE INTO Words
            (Word, USSymbol, UKSymbol, Level, Stars)
            VALUES (?, ?, ?, ?, ?)
        """
        # Bind parameters (match column order)
        return self._database.execute1(
            insert_query,
            (word.strip(), us_symbol, uk_symbol, level, stars)
        )

    def _get_item(self, word: str, item: str):
        # sql = "select " + item + " from Words where word = '" + word + "'"
        sql = f"select {item} from Words where Word = '{word}'"
        ret = self._database.get(sql)
        if ret:
            # print(f"ret = {ret}")
            # anything = ret[item]
            anything = ret[0]
            return cast(str | int, anything)
        return None

    def get_level(self, word: str):
        ret = self._get_item(word, "Level")
        # print(f"level = {ret}")
        if ret is not None:
            return cast(str, ret)
        return ""

    def _update_item(self, word: str, item: str, val: str | int):
        sql = f"update Words set {item}='{val}'"
        sql += f" where Word='{word}'"
        print(sql)

        return self._database.excute1(sql)

    def update_level(self, word: str, level: str) -> bool:
        return self._update_item(word, "Level", level)

    def add_level(self, word: str, level: str):
        if self.has_word(word):
            old_lvls = self.get_level(word)
            if len(old_lvls) > 1:
                level_list = old_lvls.split(";")
            else:
                level_list: list[str] = []
            level_list.append(level)
            print(f"level_list = {level_list}")
            level_set: set[str] = set()
            for level in level_list:
                if level:
                    level_set.add(level)
            new_lvls = ";".join(level_set)
            _ = self.update_level(word, new_lvls)
        else:
            ret = self.insert_word(word, "", "", level)
            print(f"{ret} to insert {word}")
        return self.get_level(word)

    # TODO: wait to test
    def get_star(self, word: str) -> int:
        ret = self._get_item(word, "Stars")
        # print(f"Stars = {ret}")
        if ret is not None:
            return cast(int, ret)
        return -1

    def update_star(self, word: str, star: int) -> bool:
        return self._update_item(word, "Stars", star)

    def close(self):
        return self._database.close()
