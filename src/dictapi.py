#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os
import json
from typing import cast

from flask import request, current_app
from flask.views import MethodView

# from .classbases.dictbase import DictBase
from src.logit import pv
from src.app.dictapp import DictApp
from src.app_factory import get_dict_app


class DictApi(MethodView):
    '''
        RESTful style
    '''
    def __init__(self):
        self._proj_path: str = cast(str, current_app.static_folder)
        print(f"self._proj_path = {self._proj_path}")
        self._dictapp: DictApp = get_dict_app(self._proj_path)
        self._dictbase_dict: dict[int, str] = {}
        for key, val in self._dictapp.dictbases.items():
            self._dictbase_dict[key] = val.name

    def get(self, dict_id: int | None, word: str | None):
        ''' query
        '''
        print(f"dict_id = {dict_id}, word = {word}")
        # query all dicts info, /dicts
        if dict_id is None:
            dict_list = []
            for key, val in self._dictbase_dict.items():
                dict_list.append({"id": key, "title": val})
            dicts_json = json.dumps(dict_list, ensure_ascii=False, indent=2) 
            print(f"dicts: {dicts_json}")
            return {
                'status': 'success',
                'message': 'sucess to query',
                'data': dicts_json
            }
        else:
            # dict_name = self._dictbase_dict[dict_id]
            dictbase = self._dictapp.dictbases.get(dict_id)
            if dictbase is None:
               return {
                    'status': 'fail',
                    'message': 'fail to query',
                    'data':{
                        "errcode": 404,
                        "msg": f"no dict id: {dict_id}"
                    }
                }

            # query dict detail, /dicts/{dict_id}
            if word is None:
                return {
                    'status': 'success',
                    'message': 'sucess to query',
                    'data':{
                        "name": dictbase.name,
                        "desc": dictbase.desc,
                        "cover": dictbase.cover
                    }
                }

            # query word, /dicts/{dict_id}/{word}
            dict_url, audio_url, is_new, level, stars = self._dictapp.query_word(dictbase, word)
            return {
                'status': 'success',
                'message': 'success to query',
                'data': {
                    "dict_url": dict_url if dict_id == 0 else self._convert2relativepath(dict_url),
                    "audio_url": self._convert2relativepath(audio_url),
                    "is_new": is_new,
                    "level": level,
                    "stars": stars
                }
            }

    def post(self):
        '''
            create
        '''
        form = request.json
        print(form)
        # book = Book()
        # book.book_number = form.get('book_number')
        # ...

    def delete(self, book_id):
        '''
            delete
        '''
        # book = Book.query.get(book_id)
        # db.session.delete(book)
        # db.session.commit()
        return {
            'status': 'success',
            'message': 'Sucess to delete data!'
        }

    def put(self, book_id):
        '''
            update
        '''
        # book: Book = Book.quey.get(book_id)
        # book.book_type = request.json.get('book_type')
        # ...
        # db.session.commit()
        return {
            'status': 'success',
            'message': 'Success'
        }

    def patch(self, book_id):
        '''
            partly update
        '''
        pass

    def _convert2relativepath(self, abs_path: str):
        relative_path = os.path.relpath(abs_path, self._proj_path)
        return relative_path
