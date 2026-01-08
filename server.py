#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import os
import sys
from flask import Flask

from src.dictapi import DictApi
from src.fileapi import FileApi


def get_static_folder():
    if getattr(sys, "frozen", False):
        static_folder = os.path.dirname(os.path.abspath(sys.executable))
    else:
        static_folder = os.path.abspath('./public')
    print(f"static_folder = {static_folder}")
    return static_folder


if __name__ == '__main__':
    # exe_path = os.path.dirname(os.path.abspath(__file__))
    # if getattr(sys, "frozen", False):
        # exe_path = os.path.dirname(os.path.abspath(sys.executable))
    # proj_path: str = os.path.join(exe_path, "..", "public")

    # app = Flask(__name__)
    app = Flask(__name__, static_folder=get_static_folder())
    app.json.ensure_ascii = False # flask 2.3.0以上, 解决中文乱码问题

    dict_view = DictApi.as_view('dict_api')
    app.add_url_rule('/dicts/', view_func=dict_view,
        defaults={'dict_id': None, 'word': None})
    app.add_url_rule('/dicts/<int:dict_id>/', view_func=dict_view,
        defaults={'word': None})
    app.add_url_rule('/dicts/<int:dict_id>/<string:word>/', view_func=dict_view)

    file_view = FileApi.as_view("file_api")
    app.add_url_rule('/<string:itemspath>/<string:itemname>/output/<string:filepath>', view_func=file_view)
    app.add_url_rule('/<string:itemspath>/<string:filepath>', view_func=file_view)

    app.run(host='0.0.0.0', debug=True)
