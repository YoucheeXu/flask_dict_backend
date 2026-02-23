#!/usr/bin/python3
# -*- coding: utf-8 -*-
import datetime
from typing import NamedTuple
from typing import cast
from collections.abc import Generator

from src.components.classbases.sqlite import SQLite

class WorldProgressSqlTuple(NamedTuple):
    word: str
    familiar: float
    lastdate: str | None
    nextdate: str | None


class WorldProgressTuple(NamedTuple):
    word: str
    familiar: float
    lastdate: datetime.date | None
    nextdate: datetime.date | None


class UsrProgress():
    '''
        CREATE TABLE [CET6](
            [Word] TEXT PRIMARY KEY NOT NULL, 
            [Familiar] REAL, 
            [LastDate] DATE
        );
    '''
    def __init__(self):
        self._database: SQLite = SQLite()
        self._level: str = ""
        self._progressfile: str = ""
        self._datestr_format: str = "%Y-%m-%d"

    def open(self, dictsrc: str, level: str):
        # self._level = level
        self._progressfile = dictsrc
        self._level = level
        return self._database.open(self._progressfile)

    def select_level(self, level: str):
        self._level = level

    @property
    def progressfile(self):
        return self._progressfile

    def close(self) -> bool:
        return self._database.close()

    def _get_item(self, word: str, item: str):
        # sql = "select " + item + " from Words where word = '" + word + "'"
        sql = f"select {item} from {self._level} where Word = '{word}'"
        ret = self._database.get(sql)
        anything = ret[0]
        if ret:
            return anything

        return None

    def get_lastdate(self, word: str):
        ret = cast(str | None, self._get_item(word, "LastDate"))
        if ret is not None:
            return self._str2date(ret)
        else:
            return None

    def get_familiar(self, word: str) -> int:
        return cast(int, self._get_item(word, "Familiar"))

    def _get_count(self, table: str, where: str) -> int:
        # sql = "select count(*) from Words where " + where
        sql = f"select count(*) from {table} where {where}"
        ret = self._database.get(sql)

        if ret:
            return ret[0]

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
        sql = f"DELETE FROM {self._level} WHERE Word='{wd}'"

        r = self._database.excute1(sql)
        if r:
            print(wd + " was deleted.")

    def new(self, srcfile: str, lvl: str) -> bool:
        self._database = SQLite()
        _ = self._database.open(srcfile)
        return self.new_table(lvl)

    def new_table(self, lvl: str) -> bool:
        r = self._database.excute1((f"CREATE TABLE {lvl}(Word text NOT NULL PRIMARY KEY, "
            f"Familiar REAL, LastDate datetime.date, NextDate datetime.date)"))
        if r:
            self._level = lvl
            print("Table created")
            return True

        return False

    def has_table(self, lvl: str) -> bool:
        sql = f"select count(*) from sqlite_master where type='table' and name = '{lvl}'"
        ret = self._database.get(sql)

        if ret:
            return ret['count(*)']

        return False

    def has_word(self, wd: str) -> bool:
        sql = f"select count(*) from {self._level} where Word = '{wd}'"
        ret = self._database.get(sql)

        if ret:
            if ret['count(*)'] >= 1:
                return True
            return False

        return False

    def insert_word(self, wd: str, level: str, familiar: float = 0.0):
        entry = f"'{wd}', {familiar}"
        sql = f"INSERT INTO {level} (Word, Familiar) VALUES ({entry})"
        print(sql)
        r = self._database.excute1(sql)
        if r:
            print(wd + " was inserted.")

    def _date2str(self, date: datetime.date):
        return datetime.date.strftime(date, self._datestr_format)

    def _str2date(self, date: str | None):
        if date is not None:
            return datetime.datetime.strptime(date, self._datestr_format).date()
        else:
            return None

    def _each2wordlist(self, sql: str):
        word_list: list[WorldProgressTuple] = []
        for word, familiar, lastdatestr, nextdatestr in \
                cast(Generator[WorldProgressSqlTuple, None, None], self._database.each(sql)):
            lastdate = self._str2date(lastdatestr)
            nextdate = self._str2date(nextdatestr)
            word = WorldProgressTuple(word, familiar, lastdate, nextdate)
            word_list.append(word)
        return word_list

    def get_wordlist(self, familiar: int, limit: int = -1,
            lastlastdate: datetime.date | None = None, lastdate: datetime.date | None = None) :
        table = self._level

        # get Ebbinghaus Forgetting Curve words
        if lastdate is not None:
            # sql = f"select * from {table} where level = '{level}' and lastdate <= date('{lastdate}') and lastdate >= date('{lastlastdate}') and familiar < {familiar}"
            # sql = f"select * from {table} where level = '{level}' and lastdate <= date('{lastdate}') and lastdate >= date('{lastlastdate}') and cast (Familiar as real) < {familiar}"
            sql = f"select * from {table} where lastdate <= date('{lastdate}') and lastdate >= date('{lastlastdate}') and cast (Familiar as real) < {familiar}"
            sql += " limit " + str(limit)
            # for row in cast(Generator[WorldProgressTuple, None, None], self._database.each(sql)):
                # print(f"row = {row}")
                # word_list.append(row)

        # get ancient words
        # get forgotten words
        elif lastlastdate is not None:
            # sql = f"select * from {table} where level = '{level}' and lastdate <= date('" + lastlastdate + "') and familiar < {familiar}"
            sql = f"select * from {table} where lastdate <= date('{lastlastdate}') and cast (Familiar as real) < {familiar}"
            sql += " limit " + str(limit)
            # for row in cast(Generator[WorldProgressTuple, None, None], self._database.each(sql)):
                # print(f"row = {row}")
                # word_list.append(row)
        elif limit > 0:
            # sql = f"select word from {table} where level = '{level}' and familiar <= 0 and familiar >= {familiar} limit {limit}"
            # sql = f"select * from {table} where level = '{level}' and familiar = {familiar} limit {limit}"
            sql = f"select * from {table} where cast (Familiar as real) = {familiar} limit {limit}"
            # for row in cast(Generator[WorldProgressTuple, None, None], self._database.each(sql)):
                # print(f"row = {row}")
                # word_list.append(row)

        else:
            # sql = f"select * from {table} where level = '{level}' and familiar = {familiar}"
            sql = f"select * from {table} where cast (Familiar as real) = {familiar}"
            # for row in cast(Generator[WorldProgressTuple, None, None], self._database.each(sql)):
                # print(f"row = {row}")
                # word_list.append(row)

        return self._each2wordlist(sql)

    def get_forgottenwordlst(self):
        familiar = 0
        table = self._level
        sql = f"select * from {table} where cast (Familiar as real) < {familiar}"
        return self._each2wordlist(sql)

    def get_ovrduewordlst(self, due: datetime.date):
        familiar = 10
        table = self._level
        sql = f"select * from {table} where NextDate < date('{due}') and cast (Familiar as real) < {str(familiar)}"
        return self._each2wordlist(sql)

    def get_duewordlst(self, due: datetime.date):
        familiar = 10
        table = self._level
        sql = f"select * from {table} where NextDate = date('{due}') and cast (Familiar as real) < {str(familiar)}"
        return self._each2wordlist(sql)

    def get_newwordlst(self, limit: int):
        familiar = 0
        table = self._level

        sql = f"select * from {table} where LastDate is null and cast (Familiar as real) = {str(familiar)}"
        sql += " limit " + str(limit)
        return self._each2wordlist(sql)

    def update_progress(self, word: str, familiar: int, today: datetime.date):
        table = self._level
        # entry = f"'{str(familiar)}','date("{today}")'"
        # sql = f"update {table}(familiar, lastdate) values (" + entry + ")"
        # sql = f"update {table} set Familiar={familiar}, LastDate=date('{today}')"
        sql = f"""update {table} set Familiar={familiar},
            LastDate=date('{today}')
            where Word='{word}'"""
        return self._database.excute1(sql)

    def update_progress2(self, word: str, familiar: int, last_date:
            datetime.date, next_date: datetime.date):
        table = self._level
        sql = f"""update {table} set Familiar={familiar},
                LastDate=date('{last_date}'),
                NextDate=date('{next_date}')
                where Word='{word}'
            """
        return self._database.excute1(sql)
