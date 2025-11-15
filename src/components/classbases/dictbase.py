#!/usr/bin/python3
# -*- coding: utf-8 -*-
import abc
import os
import shutil
import time
import json
from typing import TypedDict, cast


class DictCfgDict(TypedDict):
    Download: dict[str, str]


class DictBase(metaclass = abc.ABCMeta):
    def __init__(self, name: str, dictsrc: str):
        self._src: str = dictsrc
        self._name: str = name
        self._desc: str = ""
        self._cover: str = ""
        self._download: dict[str, str] | None = None

        if not os.path.isdir(dictsrc):
            dictsrc, _ = os.path.split(dictsrc)

        cfgjson = os.path.join(dictsrc, "dictcfg.json")
        # print(f"cfgjson = {cfgjson}")
        if os.path.isfile(cfgjson):
            with open(cfgjson, "r", encoding="utf-8") as f:
                json_data = f.read()
                cfgdict = cast(DictCfgDict, json.loads(json_data))
                self._download = cfgdict["Download"]

        self._tempdir: str = os.path.join(dictsrc, "output")
        if not os.path.exists(self._tempdir):
            os.makedirs(self._tempdir)

        with os.scandir(dictsrc) as entries:
            for entry in entries:
                if entry.is_file():
                    _, file_extension = os.path.splitext(entry.name)
                    if file_extension in [".css", ".js"]:
                        dest_file = os.path.join(self._tempdir, entry.name)
                        if not os.path.isfile(dest_file):
                            shutil.copy(entry.path, dest_file)

    @property
    def name(self) -> str:
        return self._name

    @property
    def src(self) -> str:
        return self._src

    @property
    def desc(self)-> str:
        return self._desc

    @desc.setter
    def desc(self, desc: str):
        self._desc = desc

    @property
    def cover(self)-> str:
        return self._cover

    @cover.setter
    def cover(self, cover: str):
        self._cover = cover

    @property
    def tempdir(self) -> str:
        return self._tempdir

    @property
    def download(self) -> dict[str, str] | None:
        return self._download

    @download.setter
    def download(self, dwnld: dict[str, str]):
        self._download = dwnld

    @abc.abstractmethod
    def open(self) -> tuple[int, str]:
        pass

    @abc.abstractmethod
    def query_word(self, word: str) -> tuple[int, str]:
        pass

    @abc.abstractmethod
    def get_wordlist(self, word_list: list[str], word: str, limit: int) -> int:
        pass

    def check_addword(self, localfile: str) -> tuple[int, str]:
        pass

    @abc.abstractmethod
    def del_word(self, word: str) -> bool:
        pass

    def close(self) -> bool:
        if os.path.exists(self._tempdir):
            shutil.rmtree(self._tempdir)
        time.sleep(1)
        if not os.path.isdir(self._tempdir):
            print(f"OK to remove {self._tempdir}")
        return True


if __name__ == '__main__':
    pass
