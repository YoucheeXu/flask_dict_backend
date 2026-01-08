#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os
from typing import override

from src.components.classbases.dictbase import DictBase
from src.components.classbases.ziparchive import ZipArchive


class AuidoArchive(DictBase):
    def __init__(self):
        super().__init__()
        self._name: str = ""
        self._src: str = ""
        self._tempdir: str = ""
        self._compression: int = 0
        self._compresslevel: int = 0
        self._download: dict[str, str] | None = None
        self._audiozip: ZipArchive = ZipArchive()

    @override
    def open(self, name: str, src: str) -> tuple[int, str]:
        # self._name = name
        # self._src = src
        # self._init_dict(self._src)
        _ = super().open(name, src)
        return self._audiozip.open(self._src)

    @override
    def close(self) -> bool:
        return True

    @override
    def query_word(self, word: str) -> tuple[int, str]:
        audiofile = os.path.join(self._tempdir, word + ".mp3")

        if os.path.isfile(audiofile):
            return 1, audiofile

        filename = word[0] + "/" + word + ".mp3"
        if self._audiozip.has_file(filename):
            audio = self._audiozip.read_file(filename)
            if audio:
                with open(audiofile, 'wb') as f:
                    _ = f.write(audio)
                return 1, audiofile
            return -1, f"Fail to read audio '{word}' in '{self._name}'!"
        if self._download is not None:
            audiourl = (self._download["URL"]).format(word)
            audiourl = audiourl.replace(" ", "%20")
            return 0, str(audiourl)

        return -1, f"no audio '{word}' in '{self._name}'"

    @override
    def check_addword(self, localfile: str) -> tuple[int, str]:
        basename = os.path.basename(localfile)
        word, _ = os.path.splitext(basename)
        filename = word[0] + "/" + word + ".mp3"
        if os.path.isfile(localfile):
            with open(localfile, "rb") as f:
                wordmp3 = f.read()
                _ = self._audiozip.add_file(filename, wordmp3)
                return 1, f"OK to add  {word} to {self._name}"
        else:
            return -1, f"Fail to add {word} to {self._name}"

    @override
    def get_wordlist(self, word: str, limit: int = 100) -> list[str]:
        return []

    @override
    def del_word(self, word: str) -> bool:
        filename = word[0] + "/" + word + ".mp3"
        return self._audiozip.del_file(filename)
