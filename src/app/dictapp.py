#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import os
import sys
import json
import logging
from typing import cast
# from zipfile import ZIP_DEFLATED, ZIP_STORED

from components.classbases.dictbase import DictBase

from components.auidoarchive import AuidoArchive
from components.gdictbase import GDictBase
from components.mdictbase import MDictBase
from components.sdictbase import SDictBase
from components.worddict import WordDict

from app.app_types import CfgDict


class DictApp:
    _dictbase_map: dict[int, DictBase] = {}
    # _dictbase_list: list[DictBase] = []
    _audiobase: AuidoArchive | None = None
    _wordbase: WordDict | None = None

    _missdict_file: str = ""
    _missaudio_file: str = ""

    _is_cfgmodified: bool = False
    _cfgfile: str = ""

    _agent_dict: dict[str, dict[str, str]] = {}

    def __init__(self, start_path: str, cfg_file: str):
        # self.__name = "Dictionary"
        self._start_path: str = os.path.abspath(start_path)
        print(f"dictApp: {self._start_path}")
        self._wronghint_file: str = os.path.join(self._start_path, "audios", "WrongHint.mp3")

        self._cfgfile = os.path.join(self._start_path, cfg_file)
        with open(self._cfgfile, "r", encoding="utf-8") as f:
            json_data = f.read()
            self._dict_cfgdict: CfgDict = json.loads(json_data)

        debug_cfg = self._dict_cfgdict["Dictionary"]["Debug"]
        debug_level = logging.INFO
        if debug_cfg["bEnable"]:
            debug_level = logging.DEBUG
        logfile = os.path.join(self._start_path, "logs", cast(str, debug_cfg["file"]))
        logfile = os.path.abspath(logfile)
        print("logfile: " + logfile)
        self._dict_logger: logging.Logger = self._create_logger("Dictionary", debug_level, logfile)
        # globalVar.Logger = self.__logger
        _ = self.read_configure(self._start_path)

    @property
    def dictbases(self):
        return self._dictbase_map

    """
    def __parse_compr(self, compr: str) -> int:
        match compr:
            case "ZIP_DEFLATED":
                return ZIP_DEFLATED
            case "ZIP_STORED":
                return ZIP_STORED
            case _:
                return ZIP_DEFLATED
    """

    def _add_dictbase(self, name: str, dictsrc: str, format: str):
        dictbase: DictBase | None = None
        # if format_["Type"] == 'ZIP':
        match format:
            case 'ZIP':
                # compr: int = self.__parse_compr(format_["Compression"])
                # dictbase_ = GDictBase(name, dictsrc, compr, format_["Compress_Level"])
                dictbase = GDictBase(name, dictsrc)
            case 'SQLite':
                dictbase = SDictBase(name, dictsrc)
            case 'mdx':
                dictbase = MDictBase(name, dictsrc)
            case _:
                raise NotImplementedError(f"Unknown dict's format: {format}!")

        ret, msg = dictbase.open()

        if ret == 1:
            self._dict_logger.info(f"Success to Open {name}")
        else:
            self._dict_logger.error(f"fail to Open {name}, due to {msg}")

        return dictbase

    # def __log(self, log_level: int, msg: str):
        # if not self.__logger:
            # return
        # match log_level:
            # case logging.DEBUG:
                # self.__logger.debug(msg)
            # case logging.INFO:
                # self.__logger.info(msg)
            # case logging.WARN:
                # self.__logger.warning(msg)
            # case logging.ERROR:
                # self.__logger.error(msg)
            # case logging.CRITICAL:
                # self.__logger.critical(msg)
            # case _:
                # self.__logger.info(msg)

    def read_configure(self, bin_path: str) -> bool:

        common = self._dict_cfgdict["Dictionary"]["common"]
        self._dict_logger.info(f"Dictionary: v{common["ver"]}")

        agent_cfg = self._dict_cfgdict['Agents']
        # bIEAgent = agent_cfg.bIEAgent
        agent_name = agent_cfg["ActiveAgent"]
        agent_info = agent_cfg['Info']
        for agent in agent_info:
            self._agent_dict[agent["Name"]] = {"ip": agent["ip"], "program": agent["Program"]}
        self._active_agent(agent_name)

        dicts_cfg = self._dict_cfgdict["DictBases"]
        # print(dict_cfg)
        for dict_cfg in dicts_cfg:
            dict_src = os.path.join(bin_path, "dicts", dict_cfg["Src"])
            dictbase = self._add_dictbase(dict_cfg["Name"], dict_src, dict_cfg["Format"])
            dictbase.desc = dict_cfg["Desc"]
            if "Cover" in dict_cfg:
                dictbase.cover = dict_cfg["Cover"]
            self._dictbase_map[dict_cfg["Id"]] = dictbase

        audio_cfg = self._dict_cfgdict['AudioBases'][0]
        audio_src = os.path.join(bin_path, "audios", audio_cfg["Src"])
        audio_format = audio_cfg['Format']
        if audio_format == 'ZIP':
            # compr = self.__parse_compr(autido_type["Compression"])
            audio_name = audio_cfg["Name"]
            # comprlvl = autido_type["CompressLevel"]
            # self.__audiobase = AuidoArchive(audio_name, dict_src, compr, comprlvl)
            self._audiobase = AuidoArchive(audio_name, audio_src)
            self._audiobase.desc = audio_cfg["Desc"]
            ret, msg = self._audiobase.open()
            if ret != 1:
                self._dict_logger.error(f"Fail to open {audio_name}, because of {msg}")

            # if "Download" in audio_cfg:
                # self._audiobase.download = audio_cfg["Download"]

        miss_cfg = self._dict_cfgdict["Miss"]
        self._missdict_file = os.path.join(self._start_path,  "logs", miss_cfg["miss_dict"])
        self._missaudio_file = os.path.join(self._start_path, "logs", miss_cfg["miss_audio"])

        worddict_cfg = self._dict_cfgdict["WordDict"]
        audio_src = os.path.join(bin_path, "dicts", worddict_cfg["Src"])

        self._wordbase = WordDict(worddict_cfg["Name"], audio_src)
        ret, msg = self._wordbase.open()
        if ret != 1:
            self._wordbase = None
            self._dict_logger.error(f"Fail to open Words.dict, because of {msg}")

       # usrsCfg = JSON.parse(JSON.stringify(self._cfg['Users']))

        # defaultUsr = self._cfg.Dictionary.User

        # for (usrCfg of usrsCfg):
        #     # progressFile = os.path.join(bin_path, usrCfg.Progress).replace(/\\/g, '/')
        #     if usrCfg.__name == defaultUsr):
        #         progressFile = os.path.join(bin_path, usrCfg.Progress)
        #         self._usrProgress = UsrProgress()
        #         self._usrProgress.Open(progressFile, "New")
        #         if self._usrProgress.ExistTable("New") == False):
        #             self._usrProgress.NewTable("New")
        #         }
        #         break
        #     }
        # }

        return True

    def _create_logger(self, loggername: str, level: int = logging.INFO,
        logfile: str | None = None) -> logging.Logger:

        logger = logging.getLogger(loggername)
        logger.setLevel(level)

        if logfile:
            # print(logFile)
            fh = logging.FileHandler(logfile, mode='w')
            fh.setLevel(level)
            fmt = '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s: %(message)s'
            fh_formatter = logging.Formatter(fmt=fmt, datefmt = "%H:%M:%S")
            fh.setFormatter(fh_formatter)
            logger.addHandler(fh)

        ch = logging.StreamHandler(stream = sys.stdout)
        ch.setLevel(level)
        fmt = "%(filename)s[L%(lineno)03d] %(levelname)s: %(message)s"
        ch_formatter = logging.Formatter(fmt=fmt, datefmt = "%H:%M:%S")
        ch.setFormatter(ch_formatter)
        logger.addHandler(ch)

        return logger

    def _active_agent(self, agent_name: str):
        agent_cfg = self._agent_dict[agent_name]
        # print(agent_cfg)
        self._dict_logger.info(f"activate agent: {agent_cfg}")

    def _record_to_file(self, file_: str, something: str):
        with open(file_, "w", encoding="utf-8") as f:
            _ = f.write(something)

    def query_word(self, dictbase_: DictBase, word: str) -> tuple[str, str, bool, str, int]:
        '''
            return [dict_url, audio_url, is_new, level, stars]
        '''

        assert self._audiobase

        is_new = False

        # dictbase_ = self.__dictbase_map[dictname]
        self._dict_logger.info(f"query word = {word} in dict = {dictbase_.name}")

        ret_dict, dict_url = dictbase_.query_word(word)
        # print(f"ret_dict: {ret_dict}, dict: {dict}")
        ret_audio, audio_url = self._audiobase.query_word(word)

        if ret_dict == 0:
            if dictbase_.download is not None:
                print(f"Going to download: {dict_url}")
                # TODO: download dict
                # self.trigger_download(dictbase_, word, dict)
            else:
                err_msg = f"Dict of {word}: {dictbase_.name} doesn't support to download.\n"
                self._record_to_file(self._missdict_file, err_msg)
                # self.Info(-1, 1, word, err_msg)
            dict_url = f"there is no {word} in {dictbase_.name}."

        if ret_dict < 0:
            self._record_to_file(self._missdict_file, dict_url)

        if ret_dict <= 0:
            dicterr_file = os.path.join(dictbase_.tempdir, word + "-error.html")
            html = f"<div class='headword'>\n\t<div class='text'>{dict_url}</div>\n</div>"
            with open(dicterr_file, "w", encoding="utf-8") as f:
                _ = f.write(html)
            dict_url = dicterr_file
        else:
            # if not self.__usr_progress.has_Word(word):
            #     ret = self.__usr_progress.insert_word(word);
            #     is_new = False
            # else:
            #     familiar = self.__usr_progress.get_item(word, "Familiar")
            #     if familiar < 10:
            #         print(word + " has been marked as new.")
            #         is_new = True
            #     else:
            #         print(word + " has been rectied.")
            #         is_new = False
            pass

        if ret_audio < 0:
            self._record_to_file(self._missaudio_file,
                "Audio of " + word + ": " + audio_url + "\n")
        elif ret_audio == 0:
            if self._audiobase.download is not None:
                print(f"Going to download: {audio_url}")
                # TODO: download audio
                # self.trigger_download(self._audiobase, word, audio_url)
            else:
                audioname = self._audiobase.name
                self._record_to_file(self._missaudio_file,
                    f"Audio of {word}: {audioname} doesn't support to download.\n")
                self._record_to_file(self._missaudio_file, "\n")

        if ret_audio <= 0:
            audio_url = self._wronghint_file

        if ret_dict < 0 or ret_audio < 0:
            self._record_to_file(self._missaudio_file, "\n")

        if ret_audio == 1:
            # self.Info(0, 2, "", "")
            pass

        if self._wordbase is not None:
            level = self._wordbase.get_level(word)
            stars = self._wordbase.get_star(word)
        else:
            level = ""
            stars = 0

        return dict_url, audio_url, is_new, level, stars

    def _save_configure(self):
        with open(self._cfgfile, "w", encoding='utf-8') as f:
            _ = f.write(json.dumps(self._dict_cfgdict, ensure_ascii=False))

    def close(self):
        for _, dictbase_ in self._dictbase_map.items():
            srcfile = dictbase_.src
            print("Start to close " + srcfile)
            ret = dictbase_.close()

            if ret:
                self._dict_logger.info(f"OK to close {srcfile}")
            else:
                self._dict_logger.error(f"Fail to close {srcfile}")

        if self._audiobase:
            ret = self._audiobase.close()
            srcfile = self._audiobase.src
            if ret:
                self._dict_logger.info(f"OK to close {srcfile}")
            else:
                self._dict_logger.error(f"Fail to close {srcfile}")

        # if self._usrProgress:
            # ret = self._usrProgress.close()
            # srcfile = self._usrProgress.src
            # if ret:
                # self.__logger.info(f"OK to close {srcfile} {msg}")
            # else:
                # self.__logger.error(f"Fail to close {srcfile}")

        if self._is_cfgmodified:
            self._save_configure()
