#!/usr/bin/python3
# -*- coding: utf-8 -*-
from typing import cast

from flask import request, Response, current_app
from flask import jsonify
from flask.views import MethodView

from src.components.classbases.dictbase import DictBase
from src.logit import pv, po, pe
from src.app.dictapp import DictApp
from src.app_factory import get_dict_app


class ReciteApi(MethodView):
    """ RESTful style

    """
    def __init__(self):
        self._proj_path: str = cast(str, current_app.static_folder)
        print(f"self._proj_path = {self._proj_path}")
        self._app: DictApp = get_dict_app(self._proj_path)

    def get(self, action: str, para: str | None) -> tuple[Response, int]:
        """ _summary_

        Args:
            action (str): _description_
            para (str | None): _description_

        Returns:
            Tuple[Response, int]: JSON response with status code:
                - 200: Processed successfully
                - 400: Bad request
                - 500: Server error
        """
        code = 400
        msg = ""
        data_dict = {}
        if para is None:
            match action:
                case "go2studymode":
                    code = 200
                    _ = self._app.go_study_mode()
                    data_dict = {
                        "num2Learn": self._app.learnum
                    }
                case "studynext":
                    code = 200
                    score, word = self._app.study_next()
                    dictbase = cast(DictBase, self._app.dictbases.get(1))
                    dict_url, audio_url, *_ = self._app.query_word(dictbase, word)
                    phonetic= ""
                    data_dict = {
                        "score": score,
                        "word": word,
                        "phonetic": phonetic,
                        "audioURL": audio_url,
                        "dictURL": dict_url,
                        "curLearnIndex": self._app.curlearnpos + 1,
                        "num2Learn": self._app.curlearnum,
                    }
                case "go2testmode":
                    code = 200
                    act2go = self._app.go_test_mode()
                    data_dict = {
                        "action": act2go,
                        "curCount": self._app.curcount,
                        "testTimes": self._app.testimes,
                        "num2Test": self._app.testnum,
                    }
                case "testnext":
                    code = 200
                    word1, word2 = self._app.test_next()
                    dictbase = cast(DictBase, self._app.dictbases.get(1))
                    _, audio1_url, *_ = self._app.query_word(dictbase, word1)
                    dict2_url, *_ = self._app.query_word(dictbase, word2)
                    data_dict = {
                        "audio1URL": audio1_url,
                        "dict2URL": dict2_url,
                        "curTestPos": self._app.curtestpos,
                        "curTestNum": self._app.curtestnum,
                    }
                case "forget":
                    code = 200
                    act2go = self._app.forget()
                    data_dict = {
                        "action": act2go,
                        "curCount": self._app.curcount,
                        "testTimes": self._app.testimes,
                        "num2Test": self._app.testnum,
                    }
                case "chop":
                    code = 200
                    act2go = self._app.chop()
                    data_dict = {
                        "action": act2go,
                        "curCount": self._app.curcount,
                        "testTimes": self._app.testimes,
                        "num2Test": self._app.testnum,
                    }
                case "saveprogress":
                    code = 200
                    self._app.save_progress()
                case _:
                    code = 400
                    msg = f"don't support to action {action}"
        else:
            if action == "start2recite":
                self._app.recite(para)
                code = 200
                data_dict = {
                    "allCount": self._app.allcount,
                    "newCount": self._app.newcount,
                    "fnshdcount": self._app.fnshdcount,
                    "inProgressCount": self._app.inprogresscount,
                    "num2Learn": self._app.learnum,
                    "num2Test": self._app.testnum
                }
            elif action == "checkinput":
                code = 200
                score, act2go = self._app.check_input(para)
                dictbase: DictBase = cast(DictBase, self._app.dictbases.get(1))
                dict_url, audio_url, *_ = self._app.query_word(dictbase, para)
                data_dict = {
                    "score": score,
                    "action": act2go,
                    "audioURL": audio_url,
                    "dictURL": dict_url,
                    "num2Learn": self._app.learnum,
                    "curCount": self._app.curcount,
                    "testTimes": self._app.testimes,
                    "num2Test": self._app.testnum,
                }
            else:
                code = 400
                msg = f"don't support to action {action} with level {para}"

        return jsonify({
            'code': code,
            'msg': msg,
            'data': data_dict
        }), code
