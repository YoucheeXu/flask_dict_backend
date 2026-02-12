#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import os
import sys
from pathlib import Path
import datetime
from enum import IntEnum, auto
import random
import json
import logging
from functools import partial
from typing import TypedDict
from typing import cast, Unpack
# from zipfile import ZIP_DEFLATED, ZIP_STORED

from src.logit import pv, po, pe
from src.components.classbases.dictbase import DictBase
from src.components.auidoarchive import AuidoArchive
from src.components.gdictbase import GDictBase
from src.components.mdictbase import MDictBase
from src.components.sdictbase import SDictBase
from src.components.worddict import WordDict
from src.components.usrprogress import WorldProgressTuple, UsrProgress
from src.app.app_types import SvrCfgDict
from src.utilities.download_queue import TaskStatus, DownloadCallbackKwargs
from src.utilities.download_queue import DownloadCallback, DownloadQueue


class WorldProgressDict(TypedDict):
    familiar: float
    lastdate: datetime.date | None
    nextdate: datetime.date | None

class ActEnum(IntEnum):
    NOACT = auto()
    STUDY_MODE = auto()
    STUDY_NEXT = auto()
    TEST_NEXT = auto()
    TEST_MODE = auto()
    FINISH = auto()

class DictApp:
    def __init__(self, start_path: str):
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
        self._cfgdict: SvrCfgDict = {}
        self._download_queue: DownloadQueue = DownloadQueue()
        self._dictlogger: logging.Logger = logging.getLogger("Dictionary")
        self._recitelogger: logging.Logger = logging.getLogger("ReciteWords")

        self._usrprogress: UsrProgress = UsrProgress()

        self._new_limit: int = 0
        self._total_limit: int = 0
        self._study_leastfamiliar: int = 0
        self._study_groupnum: int = 0
        self._test_groupnum: int = 0
        self._test_times: int = 0

        self._timeday_list: list[int] = []

        self._usrname: str = ""
        self._target: str = ""

        self._allcount: int = 0
        self._inprogresscount: int = 0
        self._newcount: int = 0
        self._fnshdcount: int = 0

        # self._today: str = datetime.date.strftime(datetime.date.today(), "%Y-%m-%d")
        self._startup_datetime: datetime.datetime = datetime.datetime.now()

        self._mode: str = "Study Mode"
        self._word_dict: dict[str, WorldProgressDict] = {}

        self._learn_list: list[str] = []
        self._curlearn_list: list[str] = []
        self._curlearn_pos:int = 0
        self._test_list: list[str] = []
        self._curtest_list: list[str] = []
        self._curtest_pos: int = 0

        self._err_count: int = 4
        self._cur_count: int = 1

        self._curword: str = ""
        self._lastWord: str = ""

        self._iscfgmodfied: bool = False

    @property
    def dictbases(self):
        return self._dictbase_map

    @property
    def allcount(self):
        return self._allcount

    @property
    def inprogresscount(self):
        return self._inprogresscount

    @property
    def newcount(self):
        return self._newcount

    @property
    def fnshdcount(self):
        return self._fnshdcount

    @property
    def learnum(self):
        return len(self._learn_list)

    @property
    def curlearnpos(self):
        return self._curlearn_pos

    @property
    def curlearnum(self):
        return len(self._curlearn_list)

    @property
    def curcount(self):
        return self._cur_count

    @property
    def testimes(self):
        return self._test_times

    @property
    def testnum(self):
        return len(self._test_list)

    @property
    def curtestpos(self):
        return self._curtest_pos

    @property
    def curtestnum(self):
        return len(self._curtest_list)

    @property
    def curword(self):
        return self._curword

    """
    def _parse_compr(self, compr: str) -> int:
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
            self._dictlogger.info(f"success to Open {dictsrc}")
        else:
            self._dictlogger.error(f"fail to Open {name}, due to {msg}")

        return dictbase

    # def _log(self, log_level: int, msg: str):
        # if not self._logger:
            # return
        # match log_level:
            # case logging.DEBUG:
                # self._logger.debug(msg)
            # case logging.INFO:
                # self._logger.info(msg)
            # case logging.WARN:
                # self._logger.warning(msg)
            # case logging.ERROR:
                # self._logger.error(msg)
            # case logging.CRITICAL:
                # self._logger.critical(msg)
            # case _:
                # self._logger.info(msg)

    def read_configure(self, cfgfile: str) -> bool:
        self._cfgfile = cfgfile
        with open(self._cfgfile, "r", encoding="utf-8") as f:
            json_data = f.read()
            self._cfgdict = json.loads(json_data)

        debug_cfg = self._cfgdict["Dictionary"]["Debug"]
        debug_level = logging.INFO
        if debug_cfg["Enable"]:
            debug_level = logging.DEBUG
        logfile = os.path.join(self._start_path, debug_cfg["File"])
        logfile = os.path.abspath(logfile)
        print("logfile: " + logfile)
        self._config_logger(self._dictlogger, logfile, debug_level)

        common = self._cfgdict["Dictionary"]["common"]
        self._dictlogger.info(f"Dictionary: v{common["ver"]}")

        agent_cfg = self._cfgdict['Agents']
        # bIEAgent = agent_cfg.bIEAgent
        agent_name = agent_cfg["ActiveAgent"]
        agent_info = agent_cfg['Info']
        for agent in agent_info:
            self._agent_dict[agent["Name"]] = {"ip": agent["ip"], "program": agent["Program"]}
        self._active_agent(agent_name)

        dicts_cfg = self._cfgdict["DictBases"]
        # print(dict_cfg)
        for dict_cfg in dicts_cfg:
            dict_src = os.path.join(self._start_path, dict_cfg["Src"])
            dictbase = self._add_dictbase(dict_cfg["Name"], dict_src, dict_cfg["Format"])
            dictbase.desc = dict_cfg["Desc"]
            if "Cover" in dict_cfg:
                dictbase.cover = dict_cfg["Cover"]
            self._dictbase_map[dict_cfg["Id"]] = dictbase

        audio_cfg = self._cfgdict['AudioBases'][0]
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
                self._dictlogger.error(f"Fail to open {audio_src}, because of {msg}")
            else:
                self._dictlogger.info(f"success to open {audio_src}")

            # if "Download" in audio_cfg:
                # self._audiobase.download = audio_cfg["Download"]

        miss_cfg = self._cfgdict["Miss"]
        self._missdict_file = os.path.join(self._start_path,  miss_cfg["miss_dict"])
        self._missaudio_file = os.path.join(self._start_path, miss_cfg["miss_audio"])

        worddict_cfg = self._cfgdict["WordDict"]
        worddict_src = os.path.join(self._start_path, worddict_cfg["Src"])

        self._wordbase = WordDict()
        ret, msg = self._wordbase.open(worddict_cfg["Name"], worddict_src)
        if ret != 1:
            self._dictlogger.error(f"Fail to open Words.dict, because of {msg}")

        # usrsCfg = JSON.parse(JSON.stringify(self._cfg['Users']))

        # defaultUsr = self._cfg.Dictionary.User

        # for usrCfg in usrsCfg:
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

        recitecfg = self._cfgdict["ReciteWords"]

        debug_cfg = recitecfg["Debug"]
        debug_level = logging.INFO
        if debug_cfg["Enable"]:
            debug_level = logging.DEBUG
        logfile = os.path.join(self._start_path, debug_cfg["File"])
        logfile = os.path.abspath(logfile)
        print("logfile: " + logfile)
        self._config_logger(self._recitelogger, logfile, debug_level)

        self._new_limit = recitecfg["General"]["NewLimit"]
        self._total_limit = recitecfg["General"]["TotalLimit"]
        self._study_leastfamiliar = recitecfg["StudyMode"]["LeastFamiliar"]
        self._study_groupnum = recitecfg["StudyMode"]["GroupNum"]
        self._test_groupnum = recitecfg["TestMode"]["GroupNum"]
        self._test_times = recitecfg["TestMode"]["Times"]

        timeinterval_list = recitecfg["TimeInterval"]
        for time_interval in timeinterval_list:
            if (time_interval["Unit"] == "d"):
                self._timeday_list.append(time_interval["Interval"])

        # read user
        self._usrname = recitecfg["LastUser"]
        usrscfg = self._cfgdict["Users"]
        for usrcfg in usrscfg:
            if self._usrname == usrcfg["Name"]:
                self._target = usrcfg["Target"]
                progress = usrcfg["Progress"]
                progressfile = os.path.join(self._start_path, progress)
                _ = self._usrprogress.open(progressfile, self._target)
                self._dictlogger.info(f"Select User: {self._usrname}, Level: {self._target}")
                self._dictlogger.info(f"Progress: {progressfile}")
                break

        return True

    def _config_logger(self, logger: logging.Logger, logfile: str = "", level: int = logging.INFO):
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

    def _active_agent(self, agent_name: str):
        agent_cfg = self._agent_dict[agent_name]
        # print(agent_cfg)
        self._dictlogger.info(f"activate agent: {agent_cfg}")

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
        self._dictlogger.info(f"query word '{word}' in dict '{dictbase_.name}'")

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
            self._dictlogger.info((f"there is no audio '{audio_url}' of '{word}' in archive "
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

        level = ""
        stars = 0
        # if self._wordbase is not None:
            # level = self._wordbase.get_level(word)
            # stars = self._wordbase.get_star(word)

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

    def add_file(self, which: str, num: int, localfile: str):
        ret = -1
        msg = f"{localfile} is no file"
        try:
            filepath = Path(localfile)
            if filepath.is_file():
                filepathstr = str(filepath)
                suffix = filepath.suffix
                if suffix == ".mp3" and which == "audios":
                    ret, msg = self._audiobase.check_addword(filepathstr)
                elif suffix == ".json" and which == "dicts":
                    ret, msg = self._dictbase_map[num].check_addword(filepathstr)
                else:
                    msg = f"unsupport file {which}/{num}/{localfile}"
                print(f"add {filepathstr}, ret = {ret}, msg: {msg}")
        except Exception as e:
            msg = str(e)
        return ret, msg

    def go_study_mode(self):
        """
        Return:
            True: study_next
            False: test_mode
        """
        self._mode = "Study Mode"
        po("Study Mode")

        self._curlearn_pos = 0
        ll = len(self._learn_list)

        if ll > self._study_groupnum:
            self._curlearn_list = self._learn_list[0:self._study_groupnum]
            del self._learn_list[0:self._study_groupnum]
        elif ll <= 0:
            self._curlearn_list = []
            return False
        else: 
            self._curlearn_list = self._learn_list[:]
            self._learn_list = []

        return True

    def study_next(self):
        ll = len(self._curlearn_list)
        score = ""
        if ll > 0:
            self._curword = self._curlearn_list[self._curlearn_pos]

            # lastDate = self._usrprogress.get_lastdate(self._curword)
            lastDate = self._word_dict[self._curword]["lastdate"]
            familiar = self._word_dict[self._curword]["familiar"]

            if lastDate is None:
                score = "New!"
            elif familiar < 0:
                score = "Forgotten"
            else:
                score = ""

            # gLogger.info("LearnPos: %d" %(self._CurLearnPos))
            # logstr = "LearnWord: %s, familiar: %.2f" %(word, self._WordsDict[word])
            # print(type(self._WordsDict[word]))
            self._recitelogger.info(f"LearnWord: {self._curword}, familiar: {familiar:.1f}")
            # gLogger.info(logstr)

            self._curlearn_pos += 1

        return score, self._curword

    def check_input(self, input_word: str):
        score = ""
        if self._mode == "Study Mode":
            if self._curlearn_pos < len(self._curlearn_list):
                # self._study_next()
                return score, ActEnum.STUDY_NEXT
            else:
                self._cur_count = 1
                self._recitelogger.info("curCount: %d" %(self._cur_count))
                self._curtest_list = self._curlearn_list[:]
                # self._go_test_mode()
                return score, ActEnum.TEST_MODE
        else:
            word = self._curtest_list[self._curtest_pos - 1]
            if input_word != word: 
                # self._score.set("Wrong!")
                score = "Wrong!"
                # self._LearnLst.append(word)
                # self._num_learn.set("%d words to Learn!" %(len(self._learn_list)))
                self._recitelogger.info("ErrCount: %d", self._err_count)
                self._recitelogger.info("Right word: %s, Wrong word: %s." %(word, input_word))
                if self._err_count == 3:
                    self._curtest_pos -= 1
                    self._err_count -= 1
                    self._word_dict[word]["familiar"] -= 0
                elif self._err_count > 0:
                    self._curtest_pos -= 1
                    self._err_count -= 1
                    self._word_dict[word]["familiar"] -= 1
                else:
                    self._err_count = 3
                    score = "Go on!"
                    self._word_dict[word]["familiar"] -= 1
                    self._learn_list.append(word)
                    self._recitelogger.info(word + " has been added in learn list.")
                    return score, ActEnum.NOACT
            else:
                score ="OK!"
                self._err_count = 3

            if self._curtest_pos < len(self._curtest_list):
                # self._word_entry.delete(0, tk.END)
                # self._test_next()
                return score, ActEnum.TEST_NEXT
            else: 
                self._cur_count += 1
                self._recitelogger.info("curCount: %d" %(self._cur_count))
                # self._go_test_mode()
                return score, ActEnum.TEST_MODE

    def go_test_mode(self) -> ActEnum:
        """

        Return:
            1: text_next
            2: study_mode
            3: test_mode
            4: finish
        """
        self._mode = "Test Mode"
        po("Test Mode")

        if len(self._test_list) > 0 and self._cur_count <= self._test_times:
            #self.__CurCount += 1
            self._curtest_pos = 0
            # random.shuffle(self._curtest_list)
            return ActEnum.TEST_NEXT
        elif len(self._curlearn_list) > 0: 
            # random.shuffle(self._learn_list
            return ActEnum.STUDY_MODE
        elif len(self._test_list) > self._test_groupnum:
            self._curtest_list = self._test_list[0: self._test_groupnum]
            del self._test_list[0: self._test_groupnum]
            self._curtest_pos = 0
            self._cur_count = 1
            return ActEnum.TEST_MODE
        elif len(self._test_list) > 0:
            self._curtest_list = self._test_list[:]
            del self._test_list[:]
            self._test_list = []
            self._curtest_pos = 0
            self._cur_count = 1
            return ActEnum.TEST_MODE
        elif len(self._learn_list) > 0:
            random.shuffle(self._learn_list)
            return ActEnum.STUDY_MODE
        else:
            return ActEnum.FINISH

    def test_next(self):
        self._curword = self._curtest_list[self._curtest_pos]

        self._recitelogger.info(f"TestWord: {self._curword}, familiar: {self._curword:.1f}")

        lastword = ""

        if self._curtest_pos >= 1:
            lastword = self._curtest_list[self._curtest_pos - 1]
        else:
            lastword = self._curtest_list[-1]

        self._curtest_pos += 1

        return self._curword, lastword

    def chop(self) -> ActEnum:
        """_summary_

        Retrun:
            0: study_next
            1: text_next
            2: study_mode
            3: test_mode
        """
        word = self._curword

        while word in self._curlearn_list:
            self._curlearn_list.remove(word)

        while word in self._learn_list:
            self._learn_list.remove(word)

        while word in self._curtest_list:
            self._curtest_list.remove(word)

        while word in self._test_list:
            self._test_list.remove(word)

        self._word_dict[word]["familiar"] = 10

        self._recitelogger.info(f"{self._curword} has been chopped!")

        if self._mode == "Study Mode":
            self._curlearn_pos -= 1
            if self._curlearn_pos <= 0:
                self._curlearn_pos = 0
            word = self._curlearn_list[self._curlearn_pos]

            if self._curlearn_pos < len(self._curlearn_list):
                return ActEnum.STUDY_NEXT
            else: 
                self._cur_count = 1
                self._recitelogger.info("curCount: %d" %(self._cur_count))
                self._curtest_list = self._curlearn_list[:]
                return ActEnum.TEST_MODE
        else:
            self._curtest_pos -= 1
            if self._curtest_pos <= 0:
                self._curtest_pos = 0
            word = self._curtest_list[self._curtest_pos]

            if self._curtest_pos < len(self._curtest_list):
                return ActEnum.TEST_NEXT
            else: 
                self._cur_count += 1
                self._recitelogger.info("curCount: %d" %(self._cur_count))
                return ActEnum.TEST_MODE

    def forget(self) -> ActEnum:
        """_summary_

        Retrun:
            0: study_next
            1: text_next
            2: study_mode
            3: test_mode
        """
        word = ""

        if self._mode == "Test Mode":
            self._curtest_pos -= 1
            if self._curtest_pos <= 0:
                self._curtest_pos = 0
            word = self._curtest_list[self._curtest_pos]

            while word in self._curtest_list:
                self._curtest_list.remove(word)

            while word in self._test_list:
                self._test_list.remove(word)

            self._word_dict[word]["familiar"] -= 5
            self._learn_list.append(word)

            self._recitelogger.info(word + " is forgotten!")

            if self._curtest_pos < len(self._curtest_list):
                return ActEnum.TEST_NEXT
            else: 
                self._cur_count += 1
                self._recitelogger.info("curCount: %d" %(self._cur_count))
                return ActEnum.TEST_MODE

        #self._WordsDict.pop(word)

        # gLogger.info("length of WordsDict: %d" %(len(self._WordsDict)))
        # # gLogger.info("WordsDict: \r\n", self._WordsDict)

        # gLogger.info("length of TestWordsList: %d" %(len(self._TestLst)))
        # # gLogger.info("TestWordsList: \r\n", self._TestLst)

        # gLogger.info("length of LearnWordsList: %d" %(len(self._LearnLst)))
        # # gLogger.info("LearnWordsList: \r\n", self._LearnLst)

        return ActEnum.NOACT

    def read_users(self):
        """self._usrDict.forEach((usrName: str, levels: Array<str>) =>:
                self._logger.info(f"User: {usrName, Levels: {levels")
                self._win.webContents.send("gui", "appendList", "usr-select", usrName)
                for (lvl in levels){
        )

        self._win.webContents.send("gui", "appendList", "usr-select", "Add more...")
        self._win.webContents.send("gui", "appendList", "lvl-select", "Add more...")

        self._win.webContents.send("gui", "displayOrHide", "SelDiag", True)
        self._win.webContents.send("gui", "displayOrHide", "bg", True)
        """
        # return self._usrsDict

    def read_allvls(self):
    #     return self._appcfg["WordsDict"]["allLvls"]
        pass

    def new_level(self, usrname: str, level: str):
        po(f"usr: {usrname}, new level: {level}")

        """
        for (usrCfg in self._cfg.Users):
            if (usrName == usrCfg.Name):
                if (self._usrprogress === undefined):
                    self._usrprogress = new UsrProgress()

                progressFile = path.join(self._startpath, usrCfg.Progress).replace(/\\/g, "/")
                self._usrprogress.Open(progressFile, level)
                if ((self._usrprogress.ExistTable(level)) == False):
                    self._usrprogress.NewTable(level)

                lvlWordsLst: list[str] = []
                ret = self._wordsDict.GetWordsLst(lvlWordsLst, level)
                if (ret):
                    for (word in lvlWordsLst):
                        # po("Going to insert: " + word)
                        self._usrprogress.InsertWord(word)
                 else:
                    return Promise.resolve<bool>(False)

                target = usrCfg.Target
                target[target.length] = level
                self._bCfgModfied = True

                return Promise.resolve<bool>(True)
        """
        return False

    # TODO:
    def new_user(self, usrname: str, level: str):
        self._iscfgmodfied = True
        # dict/XYQ.progress
        progressfile = os.path.join(self._start_path, "dict", usrname + ".progress")
        _ = self._usrprogress.new(progressfile, level)

        lvlWordsLst: list[str] = []
        # ret = self._wordsDict.GetWordsLst(lvlWordsLst, level)
        # if (ret):
        #     for (word in lvlWordsLst):
        #         # po("Going to insert: " + word)
        #         self._usrprogress.InsertWord(word)
        #     
        #  else:
        #     return Promise.resolve<bool>(False)

    def is_level_done(self, usrname: str, level: str):
        recitecfg = self._cfgdict["ReciteWords"]
        self._usrname = recitecfg["LastUser"]
        usrscfg = self._cfgdict["Users"]
        for usrcfg in usrscfg:
            if usrname == usrcfg["Name"]:
                progress = usrcfg["Progress"]
                progressfile = os.path.join(self._start_path, progress)
                self._dictlogger.info("progress: ", progressfile)

                _ = self._usrprogress.open(progressfile, level)
                num_unrecited_word1 = self._usrprogress.ge_inprogresscount(level)
                num_unrecited_word2 = self._usrprogress.get_newcount(level)
                if (num_unrecited_word1 + num_unrecited_word2 == 0):
                    return True
                else:
                    return False

        return -1, "Usr doesn't exist!"

    def recite(self):
        self._recitelogger.info("Go!")

        # update info
        # self._win.webContents.send("gui", "modifyValue", "studyLearnBtn", "正在学习")
        # self._win.webContents.send("gui", "modifyValue", "usr", usrName)
        # self._win.webContents.send("gui", "modifyValue", "level", level)

        level = self._target

        # where = "level = '" + level + "'"
        self._allcount = self._usrprogress.get_allcount(level)
        # self._win.webContents.send("gui", "modifyValue", "allCount", f"All words: {allCount}")
        self._recitelogger.info(f"All words: {self._allcount}")

        # where = "level = '" + level + "' and LastDate is null "
        self._newcount = self._usrprogress.get_newcount(level)
        # self._win.webContents.send("gui", "modifyValue", "newCount", f"New words to learn: {newCount}")
        self._recitelogger.info(f"New words to learn: {self._newcount}")

        # where = "level = '" + level + "' and familiar = 10"
        self._fnshdcount = self._usrprogress.get_fnshedcount(level)
        # self._win.webContents.send("gui", "modifyValue", "finishCount", f"Words has recited: {finishCount}")
        self._recitelogger.info(f"Words has recited: {self._fnshdcount}")

        # where = "level = '" + level + "' and familiar > 0"
        self._inprogresscount = self._usrprogress.ge_inprogresscount(level)
        # self._win.webContents.send("gui", "modifyValue", "InProgressCount", f"Words in learning: {InProgressCount}")
        self._recitelogger.info(f"Words in learning: {self._inprogresscount}")

        # ready to get words to recite
        self._learn_list.clear()
        self._test_list.clear()
        self._word_dict.clear()

        # start get words to recite
        word_list: list[WorldProgressTuple] = []

        # get forgotten words
        familiar: int = -10
        words_len: int = 0

        # get new words list (familiar < 0)
        new_word_list: list[str] = []

        while words_len < self._new_limit and familiar <= 0:
            # where = "level = '" + level + "' and familiar = " + str(familiar) + " limit " + str(limit - words_len)
            # if self.__mySDict.GetWordsLst(wdsLst, where):
            word_list = self._usrprogress.get_wordlist(familiar, self._new_limit - words_len)
            for word in word_list:
                wordprogress: WorldProgressDict = {"familiar": word.familiar, \
                    "lastdate": word.lastdate, "nextdate": word.nextdate}
                self._word_dict[word.word] = wordprogress
                new_word_list.append(word.word)
            word_list.clear()
            # words_len = len(self.__LearnLst)
            words_len = len(new_word_list)
            familiar += 1
            # self._logger2.info(familiar)
            # familiar = round(familiar, 1)

        forgotten_words_list: list[str] = []

        # self._logger2.info("length of new words: %d." %(len(newWdsLst)))
        for word in new_word_list: 
            # lastDate = self._usrprogress.get_lastdate(word)
            lastDate = self._word_dict[word]["lastdate"]
            # print(lastDate, wd)
            if lastDate is not None: 
                forgotten_words_list.append(word)
                # newWdsLst.remove(wd)
        for word in forgotten_words_list:
            new_word_list.remove(word)

        self._learn_list.extend(forgotten_words_list)
        self._recitelogger.info("length of forgotten words: %d." %(len(forgotten_words_list)))
        self._recitelogger.info("length of new words: %d." %(len(new_word_list)))

        # get old words
        timeday_list = self._timeday_list[::-1]        # reverse list
        # self._logger2.info("timeDayLst: ", timeDayLst)
        self._recitelogger.info("timeDayLst = " + "".join(list(str(timeday_list))))

        oldWordsLimit = self._total_limit - len(self._learn_list)

        familiar = 0
        words_len = 0

        # due2test_num = 0

        # lastlastdate = datetime.date.strftime(datetime.date.today(), "%Y-%m-%d") 
        lastlastdate = datetime.date.today()

        for day in timeday_list:
            selDate = datetime.date.today() - datetime.timedelta(day)
            # self._logger2.info("selDate:", selDate)
            # lastdate = datetime.date.strftime(selDate, "%Y-%m-%d")
            lastdate = selDate

            if day == timeday_list[0]:
                lastlastdate = lastdate
                # where = "level = '" + level + "' and lastdate <= date('" + lastdate + "') and familiar < 10"
            else:
                # where = "level = '" + level + "' and lastdate <= date('" + lastdate + "') and lastdate > date('" + lastlastdate + "') and familiar < 10"
                pass

            # num = self.__mySDict.GetCount(where)

            # self._logger2.info(lastdate + " day: " + str(day) + " "+ str(num) + " Words due to test.")

            # due2test_num += num

            if words_len < oldWordsLimit:
                # lastdate = datetime.date.strftime(selDate, "%Y-%m-%d")
                # self._logger2.info("lastdate: " + lastdate)
                # where = "level = '" + level + "' and lastdate <= date('" + lastdate + "') and familiar < 10 order by familiar limit " + str(oldWordsLimit - words_len)
                # where = "level = '" + level + "' and lastdate <= date('" + lastdate + "') and lastdate > date('" + lastlastdate + "') and familiar < 10 order by familiar limit " + str(oldWordsLimit - words_len)
                '''
                where += " order by familiar limit " + str(oldWordsLimit - words_len)
                if self.__mySDict.GetWordsLst(wdsLst, where):
                '''
                limit = oldWordsLimit - words_len
                word_list = self._usrprogress.get_wordlist(10, limit, lastlastdate, lastdate)
                # i = 0
                for word in word_list:
                    # self.__WordsDict[wd] = self.__mySDict.GetItem(wd, "familiar")
                    # self._word_dict[word] = self._usrprogress.get_familiar(word)
                    # self._logger2.info("word: %s, familiar: %f" %(wd, self.__WordsDict[wd]))
                    # print(wd, type(self.__WordsDict[wd]))
                    self._test_list.append(word.word)
                    # i += 1
                word_list = []
                words_len = len(self._test_list)
                # self._logger2.info("lastdate: " + lastdate + ", len: " + str(i))
            # else: break
            lastlastdate = lastdate

        # self._logger2.info("Words due to test: %d", due2test_num)

        self._test_list.extend(self._learn_list)

        words_len = self._total_limit - len(self._test_list)
        self._recitelogger.info("left %d words for new" %words_len)

        if words_len > 0: 
            self._test_list.extend(new_word_list[:words_len - 1])
            self._learn_list.extend(new_word_list[:words_len - 1])

        for word in new_word_list[words_len:]:
            if word in self._word_dict:
                del self._word_dict[word]

        random.shuffle(self._learn_list)

        self._recitelogger.info("len of all Test Words: %d." %(len(self._test_list)))
        self._test_list = list(set(self._test_list))    # remove duplicate item 
        self._recitelogger.info("len of no repeat all TestWordsList: %d." %(len(self._test_list)))
        # self._logger2.info("WordsDict = " + str(self.__WordsDict))
        # self._logger2.info("len of WordsDict: %d: " %(len(self.__WordsDict)))
        # self._logger2.info(self.__LearnLst)
        # self._logger2.info("LearnLst = " + "".join(list(str(self.__LearnLst))))
        self._recitelogger.info("len of LearnList: %d." %(len(self._learn_list)))

    def save_progress(self):
        len_worddict1 = len(self._word_dict)
        self._recitelogger.info(f"len of word dict: {len_worddict1}")
        self._recitelogger.info(f"WordsDict = {self._word_dict}")

        # remove words which hadn't be studied
        for word in self._learn_list:
            # if self.__WordsDict[word] != None: del self.__WordsDict[word]
            if word in self._word_dict:
                del self._word_dict[word]

        # remove words which hadn't be tested
        for word in self._test_list:
            if word in self._word_dict:
                del self._word_dict[word]

        if self._mode == "Study Mode": 
            for word in self._curlearn_list:
                if word in self._word_dict:
                    del self._word_dict[word]
        else:
            for word in self._curtest_list: 
                if word in self._word_dict:
                    del self._word_dict[word]

        len_worddict2 = len(self._word_dict)
        self._recitelogger.info(f"len of word dict: {len_worddict2}")
        self._recitelogger.info(f"WordsDict = {self._word_dict}")

        familiar = 0.0
        for word, wordprogress in self._word_dict.items():
            familiar = wordprogress["familiar"] + 1

            if familiar > 10:
                familiar = 10
            if familiar < -10:
                familiar = -10

            familiar = int(familiar)

            _ = self._usrprogress.update_progress(word, familiar, self._startup_datetime.date())

            """
            # calc next date
            if (lastDate != null and nextDate != null):
                intervalDay = (nextDate.valueOf() - lastDate.valueOf()) / 1000 / 60 / 60 / 24
            else:
                intervalDay = 0
                index = 0

            if intervalDay > 0:
                index = self._timeday_list.indexOf(intervalDay)
                if (index != -1):
                    index += 1
                    if (index >= self._timeday_list.length):
                        # next round
                        index = 0
                else:
                    # error
                    index = 0
            else:
                # new word
                index = 0

            if familiar < 0:
                # forgotten word
                index = 0

            nextinterval = self._timeday_list[index]
            nextdate = self._today + datetime.timedelta(nextinterval)

            self._logger.debug(f"{word}: {familiar}, lastDate: {todayStr}, nextDate: {nextdate}")
            self._usrprogress.update_progress2(word, familiar, today, nextdate)
            i += 1
            percent = (i / len_worddict2) * 100
            # self._win.webContents.send("gui", "modifyValue", "info", f"{percent:.2}% to save progress.")
            """

        num_fnshd = - len_worddict1 - len_worddict2
        self._recitelogger.info(f"Finish to receite {num_fnshd} words")

    def _save_configure(self):
        with open(self._cfgfile, "w", encoding='utf-8') as f:
            _ = f.write(json.dumps(self._cfgdict, ensure_ascii=False))

    def close(self):
        self._download_queue.wait_for_completion()

        for _, dictbase_ in self._dictbase_map.items():
            srcfile = dictbase_.src
            print("Start to close " + srcfile)
            ret = dictbase_.close()

            if ret:
                self._dictlogger.info(f"OK to close {srcfile}")
            else:
                self._dictlogger.error(f"Fail to close {srcfile}")

        if self._audiobase:
            ret = self._audiobase.close()
            srcfile = self._audiobase.src
            if ret:
                self._dictlogger.info(f"OK to close {srcfile}")
            else:
                self._dictlogger.error(f"Fail to close {srcfile}")

        if self._usrprogress:
            self.save_progress()
            ret = self._usrprogress.close()
            srcfile = self._usrprogress.progressfile
            if ret:
                self._dictlogger.info(f"OK to close {srcfile}")
            else:
                self._dictlogger.error(f"Fail to close {srcfile}")

        now = datetime.datetime.now()
        hour, reminder = divmod((now - self._startup_datetime).total_seconds(), 3600)
        minuter, reminder = divmod(reminder, 60)
        second = int(reminder)

        self._recitelogger.info(f"It cost {hour} hours, {minuter} minutes, {second} seconds.\n")

        if self._is_cfgmodified:
            self._save_configure()
