#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import os
import sys

from flask import Flask
from flask_cors import CORS

from src.dictapi import DictApi
from src.reciteapi import ReciteApi
from src.fileapi import FileApi


def get_static_folder():
    """_summary_

    Returns:
        _type_: _description_
    """
    if getattr(sys, "frozen", False):
        # static_folder = os.path.dirname(os.path.abspath(sys.executable))
        static_folder = os.path.abspath("./")
    else:
        static_folder = os.path.abspath('./public')
    print(f"static_folder = {static_folder}")
    return static_folder


def create_server():
    """_summary_
    """
    app = Flask(__name__, static_folder=get_static_folder(), static_url_path='')
    app.json.ensure_ascii = False # flask 2.3.0以上, 解决中文乱码问题

    # 核心：允许所有跨域请求（包括 file:// 协议）
    _ = CORS(
        app,
        origins="*",  # 开发环境允许所有来源，生产可限定为特定地址
        supports_credentials=True
    )

    dict_view = DictApi.as_view('dict_api')
    app.add_url_rule('/dicts/', view_func=dict_view,
        defaults={'dict_id': None, 'word': None},
        methods=['GET'],
    )
    app.add_url_rule('/dicts/<int:dict_id>/', view_func=dict_view,
        defaults={'word': None},
        methods=['GET'],
    )
    app.add_url_rule('/dicts/<int:dict_id>/<string:word>/', view_func=dict_view,
        methods=['GET'],
    )

    # words/{word}/add/level/{level}
    app.add_url_rule(
        '/words/<string:word>/add/level/<string:level>',
        view_func=dict_view,
        methods=['PATCH']
    )

    # Maximum allowed upload file size: 100MB
    app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024
    # Allowed file extensions for security control
    app.config['UPLOAD_EXTENSIONS'] = ['.json', '.mp3']

    file_view = FileApi.as_view("file_api")
    # dicts/Google/output/able.html
    # audios/Google-us/output/able.mp3
    app.add_url_rule(
        '/<string:itemspath>/<string:itemname>/output/<string:filename>',
        view_func=file_view,
        methods=['GET']
    )
    app.add_url_rule('/<string:itemspath>/<string:filename>', view_func=file_view)
    # app.add_url_rule(
        # '/<path:itemspath>',  # 捕获任意层级路径（适配你的参数结构）
        # view_func=file_view
    # )
    # dicts/1/upload/fire.json
    # audios/1/upload/fire.mp3
    app.add_url_rule(
        '/<string:itempath>/<int:itemnum>/upload/<string:filename>',
        view_func=file_view,
        methods=['POST']
    )
    # app.url_map.strict_slashes = False

    # for recite
    recite_view = ReciteApi.as_view('recite_api')
    app.add_url_rule('/recite/<string:action>/<string:para>/', view_func=recite_view,
        methods=['GET'],
    )
    app.add_url_rule('/recite/<string:action>/', view_func=recite_view,
        defaults={'para': None},
        methods=['GET'],
    )
    app.add_url_rule('/recite/<string:action>/', view_func=recite_view,
        methods=['PUT'],
    )

    app.run(host='0.0.0.0', debug=True,threaded=False) 


if __name__ == '__main__':
    create_server()
