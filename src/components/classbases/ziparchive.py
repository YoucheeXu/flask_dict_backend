#!/usr/bin/python3
#-*- encoding:utf-8 -*-
# -*- coding: utf-8 -*-
#coding=utf-8
''' 将文件归档到zip文件，并从zip文件中读取数据
v1.1    every time open zip and close    
v1.0.1    given compression format
'''
import re
from zipfile import ZipFile, BadZipFile, LargeZipFile


class ZipArchive:
    '''
        zipfile.ZipFile(file, mode='r', compression=ZIP_STORED,
            allowZip64=True, compresslevel=None)
        压缩模式有ZIP_STORED和ZIP_DEFLATED，ZIP_STORED只是存储模式，不会对文件进行压缩，
        这个是默认值，如果你需要对文件进行压缩，必须使用ZIP_DEFLATED模式
    '''
    def __init__(self):
        self._zipsrc: str = ""
        self._compression: int = 0
        self._compresslevel: int = 0

        self._file_list: list[str] = []

    def open(self, zipsrc: str) -> tuple[int, str]:
        self._zipsrc = zipsrc
        try:
            with ZipFile(self._zipsrc, 'r') as zipf:
                self._file_list = zipf.namelist()
        except (BadZipFile, LargeZipFile) as reason:
            return -1, str(reason)
        return 1, ""

    def close(self) -> bool:
        return True

    def add_file(self, filename: str, data: bytes | str) -> bool:
        with ZipFile(self._zipsrc, 'a') as zipf:
            zipf.writestr(filename, data)
        self._file_list.append(filename)
        return True

    def read_file(self, filename: str) -> bytes:
        with ZipFile(self._zipsrc, 'r') as zipf:
            file_: bytes = zipf.read(filename)
        return file_

    def has_file(self, filename: str) -> bool:
        return filename in self._file_list

    def search_file(self, pattern: str, wdmatch_lst: list[str]) -> int:
        regex = re.compile(pattern)
        for word in self._file_list:
            # gLogger.info(word)
            match = regex.search(word)
            if match:
                wdmatch_lst.append(word)
        return len(wdmatch_lst)

    def del_file(self, filename: str) -> bool:
        raise NotImplementedError("don't support to delete file: " + filename)
