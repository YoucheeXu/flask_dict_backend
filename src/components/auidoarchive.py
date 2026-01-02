#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os
from typing import override
from zipfile import ZIP_STORED

from src.components.classbases.dictbase import DictBase
from src.components.classbases.ziparchive import ZipArchive


class AuidoArchive(DictBase):
    def __init__(self, audioname: str, audiosrc: str,
        compression: int= ZIP_STORED, compresslevel: int = 0):
        super().__init__(audioname, audiosrc)

        self._audiozip: ZipArchive = ZipArchive(audiosrc, compression, compresslevel)

    @override
    def open(self) -> tuple[int, str]:
        return self._audiozip.open()

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
    def get_wordlist(self, word_list: list[str], word: str, limit: int = 100) -> int:
        return 0

    @override
    def del_word(self, word: str) -> bool:
        filename = word[0] + "/" + word + ".mp3"
        return self._audiozip.del_file(filename)


if __name__ == '__main__':
    pass
