#!/usr/bin/python3
# -*- coding: utf-8 -*-
from collections.abc import Generator
from typing import NamedTuple
from typing import override, cast

from src.components.classbases.dictbase import DictBase
from src.components.classbases.sqlite import SQLite


class WordTuple(NamedTuple):
    word: str
    symbol: str
    meaning: str
    sentences: str | None


class SDictBase(DictBase):
    '''
    Words: word, symbol, meaning, sentences, level, familiar, lastdate
    Words: word, symbol, meaning, sentences
    '''
    def __init__(self):
        super().__init__()
        self._dictbase: SQLite = SQLite()

    @override
    def open(self, name: str, src: str) -> tuple[int, str]:
        # self._name = name
        # self._src = src
        _ = super().open(name, src)
        return self._dictbase.open(self._src)

    @override
    def close(self) -> bool:
        return self._dictbase.close() and super().close()

    @override
    def query_word(self, word: str) -> tuple[int, str]:
        """
            [symbol, meaning, sentences]
        """
        # htmlfile = os.path.join(self._tempdir, word + ".html")
        # if os.path.isfile(htmlfile):
            # return 1, htmlfile
        query = "select * from Words where word = '" + word + "'"
        row = cast(WordTuple | None, self._dictbase.get(query))
        print(f"{word} = {row}")
        # word = row[0]
        # phonetic = row[1]
        # meaning = row[2]
        # sentences = row[3]
        # html = f"""
            # <!DOCtyp html>
            # <html>
                # <body>
                    # <div class = 'text'>{word}</div>
                    # <div class = 'phonetic'>{phonetic}</div>
                    # <div class = 'meaning'>{meaning}</div>
                    # <div class = 'example'>{sentences}</div>
                # </body>
            # </html>
        # """
        # with open(htmlfile, 'w', encoding="UTF-8") as f:
            # _ = f.write(html)
        if row:
            return 1, str(row)
        else:
            return -1, f"now {word} in {self._name}"

    @override
    def get_wordlist(self, word: str, limit: int = 100):
        word_list: list[str] = []
        where = "word like '" + word + "%'"
        query = "select word from Words where " + where + f"Limit {limit}"
        for row in cast(Generator[str, None, None], self._dictbase.each(query)):
            print(f"row = {row}")
            word_list.append(row)
        return word_list

    @override
    def del_word(self, word: str) -> bool:
        raise NotImplementedError("don't support to delete " + word)


if __name__ == '__main__':
    pass
