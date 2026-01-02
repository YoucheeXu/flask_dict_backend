#!/usr/bin/python3
# -*- coding: utf-8 -*-
from typing import override, cast

from src.components.classbases.dictbase import DictBase
from src.components.classbases.sqlite import SQLite


class SDictBase(DictBase):
    '''
    Words: word, symbol, meaning, sentences, level, familiar, lastdate
    Words: word, symbol, meaning, sentences
    '''
    def __init__(self, dictname: str, dictsrc: str):
        super().__init__(dictname, dictsrc)

        self._dictbase: SQLite = SQLite()

    @override
    def open(self) -> tuple[int, str]:
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
        row = cast(list[str], self._dictbase.get(query))
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
        return 1, row

    @override
    def get_wordlist(self, word_list: list[str], word: str, limit: int = 100) -> int:
        where = "word like '" + word + "%'"
        query = "select word from Words where " + where + f"Limit {limit}"
        for row in self._dictbase.each(query):
            print(f"row = {row}")
            word_list.append(row)
        return len(word_list)

    @override
    def del_word(self, word: str) -> bool:
        raise NotImplementedError("don't support to delete " + word)


if __name__ == '__main__':
    pass
