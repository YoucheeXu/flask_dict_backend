#!/usr/bin/python3
# -*- coding: UTF-8 -*-
"""
haha
"""
import os
import re
from typing import override

from src.components.classbases.dictbase import DictBase
from src.components.classbases.mdpackage import MdPackage

# def _unescape_entities(text):
    # """
    # unescape offending tags < > " &
    # """
    # text = text.replace(b'&lt', b'<')
    # text = text.replace(b'&gt', b'>')
    # text = text.replace(b'&quot', b'"')
    # text = text.replace(b'&amp', b'&')
    # return text


class MDictBase(DictBase):
    def __init__(self, name: str, dictpath: str, password: tuple[bytes, str] | None = None):
        super().__init__(name, dictpath)
        self._dictpath: str = dictpath
        self._password: tuple[bytes, str] | None = password
        self._mdd_list: list[MdPackage] = []
        with os.scandir(dictpath) as entries:
            for entry in entries:
                if entry.is_file():
                    # print(f'File: {entry.path}')
                    _, file_extension = os.path.splitext(entry.name)
                    if file_extension == ".mdx":
                        self._mdx: MdPackage = MdPackage(entry.path, False, "", self._password)
                    elif file_extension == ".mdd":
                       mdd = MdPackage(entry.path, True, "UTF-16", self._password)
                       self._mdd_list.append(mdd)
        return

    @override
    def open(self) -> tuple[int, str]:
        self._mdx.open()
        for mdd in self._mdd_list:
            mdd.open()
        return 1, ""

    @override
    def query_word(self, word: str) -> tuple[int, str]:
        htmlfile = os.path.join(self._tempdir, word + ".html")
        if os.path.isfile(htmlfile):
            return 1, htmlfile
        if self._mdx.has_record(word):
            ret, data = self._mdx.read_record(word)

            if ret == 1:
                html = "<!DOCTYPE html><html><body>" + data + "</body></html>"
                with open(htmlfile, "w", encoding="utf-8") as f:
                    _ = f.write(html)
            else:
                return ret, f"Fail to read {word} in {self._name}.mdx, because {data}"

            for mdd in self._mdd_list:
                pattern = "href='(.+?)'"
                matches = re.findall(pattern, data)
                for match in matches:
                    src = f"\\{match[0]}"
                    print(f"src = {src}")
                    if mdd.has_record(src):
                        ret, data = mdd.read_record(src)
                        if ret == 1:
                            srcfile = os.path.join(self._tempdir, src)
                            with open(srcfile, "w", encoding="utf-8") as f:
                                _ = f.write(data)
                        else:
                            return -1, f"Fail to read {src} in {self._name}.mdd"
                    else:
                        return -1, f"There is no {src} in {self._name}.mdd"
            return 1, htmlfile

        return -1, f"{word} isn't in {self._name}"

    @override
    def get_wordlist(self, word_list: list[str], word: str, limit: int = 100) -> int:
        pattern = "^" + word + ".*"
        _ = self._mdx.search_record(word_list, pattern, limit)

        return len(word_list)

    @override
    def check_addword(self, localfile: str) -> tuple[int, str]:
        raise NotImplementedError("Don't support to add record: " + localfile)

    @override
    def del_word(self, word: str) -> bool :
        raise NotImplementedError("Don't support to delete word: " + word)

    @override
    def close(self) -> bool:
        ret1 = True

        ret2 = True

        ret3 = True

        ret1 = self._mdx.close()
        for mdd in self._mdd_list:
            ret2 = ret2 and mdd.close()

        ret = ret1 and ret2 and ret3

        return ret
