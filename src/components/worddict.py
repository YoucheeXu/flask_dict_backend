#!/usr/bin/python3
# -*- coding: UTF-8 -*-
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
    def __init__(self, dictname: str, dictsrc: str):
        self._name: str = dictname
        self._src: str = dictsrc

        self._database: SQLite = SQLite()

    def open(self) -> tuple[int, str]:
        return self._database.open(self._src)

    def _get_item(self, word: str, item: str):
        # sql = "select " + item + " from Words where word = '" + word + "'"
        sql = f"select {item} from Words where Word = '{word}'"
        ret = self._database.get(sql)
        if ret:
            # print(f"ret = {ret}")
            # anything = ret[item]
            anything = ret[0]
            return cast(str | int, anything)

        return False

    # FIXME: get nothing
    def get_level(self, word: str):
        ret = self._get_item(word, "Level")
        print(f"level = {ret}")
        if ret:
            return cast(str, ret)

        return ""

    def _update_item(self, word: str, item: str, val: str | int):
        sql = f"update Words set {item}='{val}'"
        sql += f" where Word='{word}'"
        print(sql)

        return self._database.excute1(sql)

    def update_level(self, word: str, level: str) -> bool:
        return self._update_item(word, "Level", level)

    # TODO: wait to test
    def get_star(self, word: str) -> int:
        ret = self._get_item(word, "Stars")
        print(f"Stars = {ret}")
        if ret:
            return cast(int, ret)
        return -1

    def update_star(self, word: str, star: int) -> bool:
        return self._update_item(word, "Stars", star)
