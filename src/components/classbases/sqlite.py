#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os
import sqlite3
# from typing import Any


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

    def excute(self, command: str):
        _ = self._cur.execute(command)

    def commit(self):
        self._conn.commit()

    def get(self, query: str):
        # first row read
        _ = self._cur.execute(query)
        records = self._cur.fetchone()
        return records

    def each(self, query: str):
        # set of rows read
        # for row in :
            # yield row
        yield from self._cur.execute(query)

    def close(self) -> bool:
        if self._cur:
            self._cur.close()
        if self._conn:
            self._conn.close()
        return True
