#!/usr/bin/python3
# -*- coding: UTF-8 -*-
# from dataclasses import dataclass
from typing import TypedDict, NotRequired

class DictDict(TypedDict):
    Id: int
    Name: str
    Type: str
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
    common: CommonInfo
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

class SvrCfgDict(TypedDict):
    DictBases: list[DictDict]
    AudioBases: list[DictDict]
    WordDict: WordDictDict
    Users: list[UserDict]
    Agents: AgentDict
    Miss: dict[str, str]
    Dictionary: DictionaryDict
    ReciteWords: ReciteDict


# ------------------------------
# Default SvrCfgDict Instance
# ------------------------------
DEFAULT_SVR_CFG: SvrCfgDict = {
    "DictBases": [],
    "AudioBases": [
		{
			"Id": 1,
			"Name": "Google us",
			"Type": "US",
			"Desc": "US",
            "Src": "audios/Google-us/Google-us.zip",
			"Format": "ZIP"
		}
    ],

    "WordDict": {
        "Name": "Words",
        "Src": "dicts/Words.dict",
        "Level": []
    },

    "Users": [],

    "Agents": {
        "bIEAgent": False,
        "ActiveAgent": "",
        "Info": []
    },

    "Miss": {
		"miss_dict": "logs/miss.txt",
		"miss_audio": "logs/miss.txt"        
    },

    "Dictionary": {
        "common": {
            "ver": "0.0.1"            
        },
        "AudioBaseId": 1,
        "Debug": {
            "Enable": False,
            "File": "logs/Dictionary.log"
        }
    },

    "ReciteWords": {
        "common": {
            "ver": "0.0.1"
        },
		"General": {
			"NewLimit": 50,
			"TotalLimit": 200
		},
		"StudyMode": {
			"LeastFamiliar": 0,
			"GroupNum": 10
		},
		"TestMode": {
			"GroupNum": 10,
			"Times": 4
		},
        "TimeInterval": [
			{
				"Interval": 5,
				"Unit": "m"
			},
			{
				"Interval": 30,
				"Unit": "m"
			},
			{
				"Interval": 12,
				"Unit": "h"
			},
			{
				"Interval": 1,
				"Unit": "d"
			},
			{
				"Interval": 2,
				"Unit": "d"
			},
			{
				"Interval": 4,
				"Unit": "d"
			},
			{
				"Interval": 7,
				"Unit": "d"
			},
			{
				"Interval": 15,
				"Unit": "d"
			}
        ],
        "AudioBaseId": 0,
        "DictBaseId": 0,
        "Debug": {
            "Enable": False,
            "File": "logs/ReciteWords.log"
        }
    }
}