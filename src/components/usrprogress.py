#!/usr/bin/python3
# -*- coding: utf-8 -*-
'''
To-Do:
* support create dict and initialize it
'''
from typing import Any
import datetime

from components.classbases.sqlite import SQLite


class UsrProgress():
    '''
    Words: word, symbol, meaning, sentences, level, familiar, lastdate
    Words: word, level, familiar, lastdate
    '''
    __level: str = ""

    def __init__(self, dictsrc: str):
        self.__database: SQLite = SQLite()
        self.__progressfile: str = dictsrc

    def open(self) -> tuple[int, str]:
        return self.__database.open(self.__progressfile)

    def close(self) -> bool:
        return self.__database.close()

    def _get_item(self, word: str, item: str) -> Any:
        # sql = "select " + item + " from Words where word = '" + word + "'"
        sql = f"select {item} from {self.__level} where Word = '{word}'"
        ret = self.__database.get(sql)
        anything = ret[item]
        if ret:
            return anything

        return False

    def get_lastdate(self, word: str):
        return datetime.datetime.date(self._get_item(word, "LastDate"))

    def get_familiar(self, word: str) -> int:
        return int(self._get_item(word, "Familiar"))

    def _get_count(self, table: str, where: str) -> int:
        # sql = "select count(*) from Words where " + where
        sql = f"select count(*) from {table} where {where}"
        ret = self.__database.get(sql)

        if ret:
            return ret

        return 0

    def get_allcount(self, level: str) -> int:
        # where = "level = '" + level + "'"
        where = "Familiar is not null"
        return self._get_count(level, where)

    def ge_inprogresscount(self, level: str) -> int:
        # where = "level = '" + level + "' and familiar > 0"
        # where = "LastDate is not null and cast (Familiar as real) < 10"
        where = "cast (Familiar as real) < 10 and LastDate is not null"
        return self._get_count(level, where)

    def get_needcount(self, level: str):
        # where = "level = '" + level + "' and familiar > 0"
        where = f"level = '{level}' and familiar > 0"
        return self._get_count(level, where)

    def get_newcount(self, level: str) -> int:
        # where = "level = '" + level + "' and LastDate is null "
        where = "LastDate is null and cast (Familiar as real) < 10"
        return self._get_count(level, where)

    def get_fnshedcount(self, level: str) -> int:
        # where = "level = '" + level + "' and familiar = 10"
        where = "cast (Familiar as real) >= 10"
        return self._get_count(level, where)

    # def get_wordlist(self, *args) -> int:
        # word_list = args[0]
        # level = args[1]
        # familiar = args[-2]
        # limit = args[-1]
        # if len(args) == 4:
            # # (word_list, level, familiar, limit)
            # where = "level = '" + level + "' and familiar = " + \
                # str(familiar) + " limit " + str(limit)
            # self.__database.get_wordlist(word_list, where)
        # elif len(args) == 6:
            # # (word_list, level, lastdate, lastlastdate, familiar, limit)
            # lastdate = args[2]
            # lastlastdate = args[3]
            # where = "level = '" + level + "' and lastdate <= datetime.date('" + lastdate + \
                # "') and lastdate >= datetime.date('" + lastlastdate + "') and familiar < " + str(familiar)
            # where += " order by familiar limit " + str(limit)

            # self.__database.get_wordlist(word_list, where)

        # return len(word_list)

    # def update_progress(self, word: str, familiar: int, today):
        # itm_list = ['familiar', 'lastdate']
        # valLst = []
        # valLst.append(str(familiar))
        # valLst.append("datetime.date('" + self.__today + "')")
        # val_list = [str(familiar), "datetime.date('" + today + "')"]
        # value_dict = dict(zip(itm_list, val_list))

        # self.__database.update(word, value_dict)

    def del_word(self, wd: str):
        sql = f"DELETE FROM {self.__level} WHERE Word='{wd}'"

        r = self.__database.excute1(sql)
        if r:
            print(wd + " was deleted.")

    def new(self, srcfile: str, lvl: str) -> bool:
        self.__database = SQLite()
        _ = self.__database.open(srcfile)
        return self.new_table(lvl)

    def new_table(self, lvl: str) -> bool:
        r = self.__database.excute1((f"CREATE TABLE {lvl}(Word text NOT NULL PRIMARY KEY, "
            f"Familiar REAL, LastDate datetime.date, NextDate datetime.date)"))
        if r:
            self.__level = lvl
            print("Table created")
            return True

        return False

    def has_table(self, lvl: str) -> bool:
        sql = f"select count(*) from sqlite_master where type='table' and name = '{lvl}'"
        ret = self.__database.get(sql)

        if ret:
            return ret['count(*)']

        return False

    def has_word(self, wd: str) -> bool:
        sql = f"select count(*) from {self.__level} where Word = '{wd}'"
        ret = self.__database.get(sql)

        if ret:
            if ret['count(*)'] >= 1:
                return True
            return False

        return False

    def insert_word(self, wd: str):
        entry = f"'{wd}', 0"
        sql = f"INSERT INTO {self.__level} (Word, Familiar) VALUES ({entry})"
        print(sql)
        r = self.__database.excute1(sql)
        if r:
            print(wd + " was inserted.")

    def get_wordslst(self, args: list[Any]) -> int:
        word_list: list[str] = args[0]
        # familiar: int = args[-2]
        familiar: int = 0
        limit: int = 0
        # get words
        if len(args) == 2:
            # (word_list, familiar)
            familiar = args[1]
            # sql = "select * from Words where level = '" + level + "' and familiar = " + str(familiar)
            # sql = f"select * from {self.__level} where cast (Familiar as real) = {str(familiar)}"
            sql = f"select Word from {self.__level} where cast (Familiar as real) = {str(familiar)}"
            for row in self.__database.each(sql):
                print(f"row = {row}")
                word_list.append(row)

        elif len(args) == 3:
            # (word_list, familiar, limit)
            familiar = args[1]
            limit = args[2]
            # sql = "select word from Words where level = '" + level + "' and familiar <= 0 and familiar >= " + str(familiar) + " limit " + str(limit)
            # sql = "select * from Words where level = '" + level + "' and familiar = " + str(familiar) + " limit " + str(limit)
            sql = f"select * from {self.__level} where cast (Familiar as real) = {str(familiar)} limit {str(limit)}"
            for row in self.__database.each(sql):
                print(f"row = {row}")
                word_list.append(row)

        # get ancient words
        # get forgotten words
        elif len(args) == 4:
            # (word_list, lastlastdate, familiar, limit)
            lastlastdate = args[1]
            familiar = args[2]
            limit = args[3]
            # sql = "select * from Words where level = '" + level + "' and lastdate <= datetime.date('" + lastlastdate + "') and familiar < " + str(familiar)
            sql = f"select * from {self.__level} where lastdate <= datetime.date('{lastlastdate}') and cast (Familiar as real) < {str(familiar)}"
            sql += " limit " + str(limit)

            for row in self.__database.each(sql):
                print(f"row = {row}")
                word_list.append(row)

        # get Ebbinghaus Forgetting Curve words
        elif len(args) == 5:
            # (word_list, lastdate, lastlastdate, familiar, limit)
            lastdate = args[1]
            lastlastdate = args[2]
            familiar = args[3]
            limit = args[4]

            # sql = "select * from Words where level = '" + level + "' and lastdate <= datetime.date('" + lastdate + "') and lastdate >= datetime.date('" + lastlastdate + "') and familiar < " + str(familiar)
            # sql = "select * from Words where level = '" + level + "' and lastdate <= datetime.date('" + lastdate + "') and lastdate >= datetime.date('" + lastlastdate + "') and cast (Familiar as real) < " + str(familiar)
            sql = f"select * from {self.__level} where lastdate <= datetime.date('{lastdate}') and lastdate >= datetime.date('{lastlastdate}') and cast (Familiar as real) < {str(familiar)}"
            sql += " limit " + str(limit)

            for row in self.__database.each(sql):
                print(f"row = {row}")
                word_list.append(row)

        return len(word_list)

    def get_forgottenwordlst(self, word_list: list[str]) -> int:
        familiar = 0
        sql = f"select * from {self.__level} where cast (Familiar as real) < {str(familiar)}"

        for row in self.__database.each(sql):
            print(f"row = {row}")
            word_list.append(row)

        return len(word_list)

    def get_ovrduewordlst(self, word_list: list[str], today: str) -> int:
        familiar = 10
        sql = f"select * from {self.__level} where NextDate < datetime.date('{today}') and cast (Familiar as real) < {str(familiar)}"
        for row in self.__database.each(sql):
            print(f"row = {row}")
            word_list.append(row)

        return len(word_list)

    def get_duewordlst(self, word_list: list[str], today: str) -> int:
        familiar = 10
        sql = f"select * from {self.__level} where NextDate = datetime.date('{today}') and cast (Familiar as real) < {str(familiar)}"

        for row in self.__database.each(sql):
            print(f"row = {row}")
            word_list.append(row)

        return len(word_list)

    def get_newwordlst(self, word_list: list[str], limit: int) -> int:
        familiar = 0

        sql = f"select * from {self.__level} where LastDate is null and cast (Familiar as real) = {str(familiar)}"
        sql += " limit " + str(limit)

        for row in self.__database.each(sql):
            print(f"row = {row}")
            word_list.append(row)

        return len(word_list)

    def update_progress(self, word: str, familiar: int, today: str) -> bool:
        # entry = f"'{str(familiar)}','datetime.date("{today}")'"
        # sql = "update Words(familiar, lastdate) values (" + entry + ")"

        # sql = f"update Words set Familiar={familiar}, LastDate=datetime.date('{today}')"
        sql = f"update {self.__level} set Familiar={familiar}, LastDate=datetime.date('{today}')"
        sql += f" where Word='{word}'"

        return self.__database.excute1(sql)

    def update_progress2(self, word: str, familiar: int, last_data: str, next_date: str) -> bool:
        sql = f"update {self.__level} set Familiar={familiar}, LastDate=datetime.date('{last_data}'), NextDate=datetime.date('{next_date}')"
        sql += f" where Word='{word}'"
        print(sql)

        return self.__database.excute1(sql)
