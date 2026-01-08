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


class CommonInfo(TypedDict):
    ver: str


class GeneralCfg(TypedDict):
    NewLimit: int
    TotalLimit: int


class StudyModeCfg(TypedDict):
    LeastFamiliar: int
    GroupNum: int


class TestModeCfg(TypedDict):
    GroupNum: int
    Times: int


class TimeIntervalCfg(TypedDict):
    Interval: int
    Unit: str


class DebugCfg(TypedDict):
    Enable: bool
    File: str


class DictionaryDict(TypedDict):
    common: dict[str, str]
    AudioBaseId: int
    Debug: DebugCfg


class ReciteDict(TypedDict):
    common: CommonInfo
    General: GeneralCfg
    StudyMode: StudyModeCfg
    TestMode: TestModeCfg
    TimeInterval: list[TimeIntervalCfg]
    AudioBaseId: int
    Debug: DebugCfg


class SvrCfgDict(TypedDict):
    DictBases: list[DictDict]
    AudioBases: list[DictDict]
    WordDict: WordDictDict
    DictBase: int
    Users: list[UserDict]
    Agents: AgentDict
    Miss: dict[str, str]
    Dictionary: DictionaryDict
    Recite: ReciteDict

class DictBaseFormat(TypedDict):
    Type: str
    comprehension: NotRequired[int]
    CompressLevel: NotRequired[int]


class DictBaseCfg(TypedDict):
    Name: str
    File: str
    Format: DictBaseFormat


class UsrCfg(TypedDict):
    Name: str
    Target: str
    Progress: str


class UserCfg(TypedDict):
    LastUser: str
    Users: list[UsrCfg]


class ReciteCfg(TypedDict):
    Common: CommonInfo
    General: GeneralCfg
    StudyMode: StudyModeCfg
    TestMode: TestModeCfg
    TimeInterval: list[TimeIntervalCfg]
    Debug: DebugCfg
    DictBase: dict[str, DictBaseCfg]
    User: UserCfg
