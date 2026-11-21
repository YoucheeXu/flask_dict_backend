#!/usr/bin/python3
# -*- coding: UTF-8 -*-
"""
haha
"""
import os
import re
from html.parser import HTMLParser
from typing import cast, override

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

class LinkFinder(HTMLParser):
    def __init__(self):
        super().__init__()
        self._links: list[str] = []

    @property
    def links(self):
        return self._links

    @override
    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for k, v in attrs:
            if k == "href" and v:
                self._links.append(v)
        # return super().handle_starttag(tag, attrs)

class MDictBase(DictBase):
    def __init__(self, password: tuple[bytes, str] | None = None):
        super().__init__()
        self._password: tuple[bytes, str] | None = None
        self._mdd_list: list[MdPackage] = []

    @override
    def open(self, name: str, src: str) -> tuple[int, str]:
        _ = super().open(name, src)
        with os.scandir(self._src) as entries:
            for entry in entries:
                if entry.is_file():
                    # print(f'File: {entry.path}')
                    _, file_extension = os.path.splitext(entry.name)
                    if file_extension == ".mdx":
                        self._mdx: MdPackage = MdPackage(entry.path, False, "", self._password)
                    elif file_extension == ".mdd":
                       mdd = MdPackage(entry.path, True, "UTF-16", self._password)
                       self._mdd_list.append(mdd)
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
            ret, mdxdata = cast(tuple[int, str], self._mdx.read_record(word))

            if ret == 1:
                html = "<!DOCTYPE html><html><body>" + mdxdata + "</body></html>"
                with open(htmlfile, "w", encoding="utf-8") as f:
                    _ = f.write(html)
            else:
                return ret, f"Fail to read {word} in {self._name}.mdx, because {mdxdata}"

            for mdd in self._mdd_list:
                # pattern = "href='(.+?)'"
                # matches = re.findall(pattern, data)
                p = LinkFinder()
                p.feed(mdxdata)
                matches = p.links
                # pv(matches)
                for match in matches:
                    # src = f"\\{match[0]}"
                    srcfile = os.path.join(self._tempdir, match)
                    # pv(srcfile)
                    if os.path.isfile(srcfile):
                        continue
                    src = f"\\{match}"
                    if mdd.has_record(src):
                        ret, mdddata = cast(tuple[int, bytes], mdd.read_record(src))
                        if ret == 1:
                            # with open(srcfile, "w", encoding="utf-8") as f:
                            with open(srcfile, "wb") as f:
                                _ = f.write(mdddata)
                        else:
                            return -1, f"Fail to read {src} in {self._name}.mdd"
                    else:
                        return -1, f"There is no {src} in {self._name}.mdd"
            return 1, htmlfile

        return -1, f"{word} isn't in {self._name}"

    @override
    def get_wordlist(self, word: str, limit: int = 100):
        pattern = "^" + word + ".*"
        return self._mdx.search_record(pattern, limit)

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
