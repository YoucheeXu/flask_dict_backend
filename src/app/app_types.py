#!/usr/bin/python3
# -*- coding: UTF-8 -*-
# from dataclasses import dataclass
from typing import TypedDict, NotRequired


# class DictCfgDict(TypedDict):
    # Download: NotRequired[dict[str, str]]


class DictDict(TypedDict):
    Id: int
    Name: str
    Typ: str
    Src: str
    Desc: str
    Cover: NotRequired[str]
    Format: str


class WordDictDict(TypedDict):
    Name: str
    Src: str
    Level: list[str]


class UserDict(TypedDict):
    Name: str
    Target: list[str]
    Progress: str


class AgentDict(TypedDict):
    bIEAgent: bool
    ActiveAgent: str
    Info: list[dict[str, str]]


class DictionaryDict(TypedDict):
    common: dict[str, str]
    AudioBase: int
    Debug: dict[str, bool | str]


class ReciteDict(TypedDict):
    common: dict[str, str]
    StudyMode: dict[str, int]
    TestMode: dict[str, int]
    General: dict[str, int]
    TimeInterval: list[dict[str, str | int]]
    AudioBase: int
    Debug: dict[str, bool | str]


class CfgDict(TypedDict):
    DictBases: list[DictDict]
    AudioBases: list[DictDict]
    WordDict: WordDictDict
    DictBase: int
    Users: list[UserDict]
    Agents: AgentDict
    Miss: dict[str, str]
    Dictionary: DictionaryDict
    Recite: ReciteDict
