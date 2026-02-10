#!/usr/bin/python3
# -*- coding: UTF-8 -*-
# from dataclasses import dataclass
from typing import TypedDict, NotRequired

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
    Target: str
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
    DictBaseId: int
    Debug: DebugCfg
    LastUser: str

class SvrCfgDict(TypedDict):
    DictBases: list[DictDict]
    AudioBases: list[DictDict]
    WordDict: WordDictDict
    Users: list[UserDict]
    Agents: AgentDict
    Miss: dict[str, str]
    Dictionary: DictionaryDict
    ReciteWords: ReciteDict
