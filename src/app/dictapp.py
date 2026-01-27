#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import os
import sys
import json
import logging
from functools import partial
from typing import cast, Unpack
# from zipfile import ZIP_DEFLATED, ZIP_STORED

from src.components.classbases.dictbase import DictBase
from src.components.auidoarchive import AuidoArchive
from src.components.gdictbase import GDictBase
from src.components.mdictbase import MDictBase
from src.components.sdictbase import SDictBase
from src.components.worddict import WordDict
from src.app.app_types import SvrCfgDict
from src.utilities.download_queue import TaskStatus, DownloadCallbackKwargs
from src.utilities.download_queue import DownloadCallback, DownloadQueue


class DictApp:
    def __init__(self, start_path: str):
        self._appname: str = "Dictionary"
        self._start_path: str = os.path.abspath(start_path)
        print(f"dictApp: {self._start_path}")

        self._dictbase_map: dict[int, DictBase] = {}
        # self._dictbase_list: list[DictBase] = []
        self._audiobase: AuidoArchive = AuidoArchive()
        self._wordbase: WordDict = WordDict()

        self._missdict_file: str = ""
        self._missaudio_file: str = ""

        self._is_cfgmodified: bool = False
        self._cfgfile: str = ""

        self._agent_dict: dict[str, dict[str, str]] = {}

        self._wronghint_file: str = os.path.join(self._start_path, "audios", "WrongHint.mp3")
        self._dict_cfgdict: SvrCfgDict = {}
        self._download_queue: DownloadQueue = DownloadQueue()
        self._logger: logging.Logger = logging.getLogger(self._appname)

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
                dictbase = GDictBase()
            case 'SQLite':
                dictbase = SDictBase()
            case 'mdx':
                dictbase = MDictBase()
            case _:
                raise NotImplementedError(f"Unknown dict's format: {format}!")

        ret, msg = dictbase.open(name, dictsrc)

        if ret == 1:
            self._logger.info(f"success to Open {dictsrc}")
        else:
            self._logger.error(f"fail to Open {name}, due to {msg}")

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

    def read_configure(self, cfgfile: str) -> bool:
        self._cfgfile = cfgfile
        with open(self._cfgfile, "r", encoding="utf-8") as f:
            json_data = f.read()
            self._dict_cfgdict = json.loads(json_data)

        debug_cfg = self._dict_cfgdict["Dictionary"]["Debug"]
        debug_level = logging.INFO
        if debug_cfg["Enable"]:
            debug_level = logging.DEBUG
        logfile = os.path.join(self._start_path, debug_cfg["File"])
        logfile = os.path.abspath(logfile)
        print("logfile: " + logfile)
        self._config_logger(logfile, debug_level)

        common = self._dict_cfgdict["Dictionary"]["common"]
        self._logger.info(f"Dictionary: v{common["ver"]}")

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
            dict_src = os.path.join(self._start_path, dict_cfg["Src"])
            dictbase = self._add_dictbase(dict_cfg["Name"], dict_src, dict_cfg["Format"])
            dictbase.desc = dict_cfg["Desc"]
            if "Cover" in dict_cfg:
                dictbase.cover = dict_cfg["Cover"]
            self._dictbase_map[dict_cfg["Id"]] = dictbase

        audio_cfg = self._dict_cfgdict['AudioBases'][0]
        audio_src = os.path.join(self._start_path, audio_cfg["Src"])
        audio_format = audio_cfg['Format']
        if audio_format == 'ZIP':
            # compr = self.__parse_compr(autido_type["Compression"])
            audio_name = audio_cfg["Name"]
            # comprlvl = autido_type["CompressLevel"]
            # self.__audiobase = AuidoArchive(audio_name, dict_src, compr, comprlvl)
            self._audiobase = AuidoArchive()
            self._audiobase.desc = audio_cfg["Desc"]
            ret, msg = self._audiobase.open(audio_name, audio_src)
            if ret != 1:
                self._logger.error(f"Fail to open {audio_src}, because of {msg}")
            else:
                self._logger.info(f"success to open {audio_src}")

            # if "Download" in audio_cfg:
                # self._audiobase.download = audio_cfg["Download"]

        miss_cfg = self._dict_cfgdict["Miss"]
        self._missdict_file = os.path.join(self._start_path,  miss_cfg["miss_dict"])
        self._missaudio_file = os.path.join(self._start_path, miss_cfg["miss_audio"])

        worddict_cfg = self._dict_cfgdict["WordDict"]
        worddict_src = os.path.join(self._start_path, worddict_cfg["Src"])

        self._wordbase = WordDict()
        ret, msg = self._wordbase.open(worddict_cfg["Name"], worddict_src)
        if ret != 1:
            self._logger.error(f"Fail to open Words.dict, because of {msg}")

       # usrsCfg = JSON.parse(JSON.stringify(self._cfg['Users']))

        # defaultUsr = self._cfg.Dictionary.User

        # for (usrCfg of usrsCfg):
        #     # progressFile = os.path.join(self._start_path, usrCfg.Progress).replace(/\\/g, '/')
        #     if usrCfg.__name == defaultUsr):
        #         progressFile = os.path.join(self._start_path, usrCfg.Progress)
        #         self._usrProgress = UsrProgress()
        #         self._usrProgress.Open(progressFile, "New")
        #         if self._usrProgress.ExistTable("New") == False):
        #             self._usrProgress.NewTable("New")
        #         }
        #         break
        #     }
        # }

        return True

    def _config_logger(self, logfile: str = "", level: int = logging.INFO):
        self._logger.setLevel(level)

        if logfile:
            # print(logFile)
            fh = logging.FileHandler(logfile, mode='w')
            fh.setLevel(level)
            fmt = '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s: %(message)s'
            fh_formatter = logging.Formatter(fmt=fmt, datefmt = "%H:%M:%S")
            fh.setFormatter(fh_formatter)
            self._logger.addHandler(fh)

        ch = logging.StreamHandler(stream = sys.stdout)
        ch.setLevel(level)
        fmt = "%(filename)s[L%(lineno)03d] %(levelname)s: %(message)s"
        ch_formatter = logging.Formatter(fmt=fmt, datefmt = "%H:%M:%S")
        ch.setFormatter(ch_formatter)
        self._logger.addHandler(ch)

    def _active_agent(self, agent_name: str):
        agent_cfg = self._agent_dict[agent_name]
        # print(agent_cfg)
        self._logger.info(f"activate agent: {agent_cfg}")

    def _record2file(self, file_: str, something: str):
        with open(file_, "w", encoding="utf-8") as f:
            _ = f.write(something)

    def query_word(self, dictbase_: DictBase, word: str) -> tuple[str, str, bool, str, int]:
        '''
            return [dict_url, audio_url, is_new, level, stars]
        '''

        assert self._audiobase

        is_new = False

        # dictbase_ = self.__dictbase_map[dictname]
        self._logger.info(f"query word '{word}' in dict '{dictbase_.name}'")

        ret_dict, dict_url = dictbase_.query_word(word)
        # print(f"ret_dict: {ret_dict}, dict: {dict}")
        ret_audio, audio_url = self._audiobase.query_word(word)

        if ret_dict == 0:
            if dictbase_.download is not None:
                print(f"Going to download: {dict_url}")
                dict_url = dictbase_.download["URL"].format(word)
                save_path = dictbase_.download["SavePath"].format(word)
                callback = cast(DownloadCallback,
                    partial(self._download_callback, dictbase_, f"word '{word}'"))
                _ = self._download_queue.add_task(
                    url=dict_url,
                    save_path=save_path,
                    task_callback=callback)
            else:
                err_msg = f"Dict of {word}: {dictbase_.name} doesn't support to download.\n"
                self._record2file(self._missdict_file, err_msg)
                # self.Info(-1, 1, word, err_msg)
            dict_url = f"there is no {word} in {dictbase_.name}."

        if ret_dict < 0:
            self._record2file(self._missdict_file, dict_url)

        if ret_dict <= 0:
            dicterr_file = os.path.join(dictbase_.tempdir, word + "-error.html")
            html = f"<div class='headword'>\n\t<div class='text'>{dict_url}</div>\n</div>"
            with open(dicterr_file, "w", encoding="utf-8") as f:
                _ = f.write(html)
            dict_url = dicterr_file
        else:
            # if not self._usr_progress.has_Word(word):
            #     ret = self._usr_progress.insert_word(word);
            #     is_new = False
            # else:
            #     familiar = self._usr_progress.get_item(word, "Familiar")
            #     if familiar < 10:
            #         print(word + " has been marked as new.")
            #         is_new = True
            #     else:
            #         print(word + " has been rectied.")
            #         is_new = False
            pass

        audioname = self._audiobase.name
        if ret_audio < 0:
            self._record2file(self._missaudio_file,
                "Audio of " + word + ": " + audio_url + "\n")
            self._logger.info((f"there is no audio '{audio_url}' of '{word}' in archive "
                f"'{self._audiobase.name}'"))
        elif ret_audio == 0:
            if self._audiobase.download is not None:
                print(f"Going to download: {audio_url}")
                # TODO: download audio
                # self.trigger_download(self._audiobase, word, audio_url)
            else:
                self._record2file(self._missaudio_file,
                    f"doesn't support downloading audio '{audio_url}' of '{word}'\n")
                self._record2file(self._missaudio_file, "\n")

        if ret_audio <= 0:
            audio_url = self._wronghint_file

        if ret_dict < 0 or ret_audio < 0:
            self._record2file(self._missaudio_file, "\n")

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

    def _download_callback(self, db: DictBase, msg: str,
            **kwargs: Unpack[DownloadCallbackKwargs]):
        status = kwargs['status']
        print(f"{msg} download: {status.name}")
        if status == TaskStatus.SUCCEEDED:
            save_path = kwargs['save_path']
            ret, msg = db.check_addword(save_path)
            print(f"{'fail' if ret <=0 else 'success'}: {msg}")
            os.remove(save_path)

    def _save_configure(self):
        with open(self._cfgfile, "w", encoding='utf-8') as f:
            _ = f.write(json.dumps(self._dict_cfgdict, ensure_ascii=False))

    def close(self):
        self._download_queue.wait_for_completion()

        for _, dictbase_ in self._dictbase_map.items():
            srcfile = dictbase_.src
            print("Start to close " + srcfile)
            ret = dictbase_.close()

            if ret:
                self._logger.info(f"OK to close {srcfile}")
            else:
                self._logger.error(f"Fail to close {srcfile}")

        if self._audiobase:
            ret = self._audiobase.close()
            srcfile = self._audiobase.src
            if ret:
                self._logger.info(f"OK to close {srcfile}")
            else:
                self._logger.error(f"Fail to close {srcfile}")

        # if self._usrProgress:
            # ret = self._usrProgress.close()
            # srcfile = self._usrProgress.src
            # if ret:
                # self._logger.info(f"OK to close {srcfile} {msg}")
            # else:
                # self._logger.error(f"Fail to close {srcfile}")

        if self._is_cfgmodified:
            self._save_configure()
