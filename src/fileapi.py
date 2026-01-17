#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os
from typing import cast

from flask import request, Response, redirect, url_for, current_app
from flask import send_from_directory
from flask.views import MethodView

from src.logit import pv, po, pe


class FileApi(MethodView):
    """ RESTful style

    """
    def __init__(self):
        self._proj_path: str = cast(str, current_app.static_folder)

    def get(self, itemspath: str, itemname: str = "", filename: str = ""):
        """ query

        Args:
            itemspath (str): _description_
            itemname (str, optional): _description_. Defaults to "".
            filename (str, optional): _description_. Defaults to "".

        Returns:
            _type_: _description_
        """
        print(f"itemspath = {itemspath}")
        print(f"itemname = {itemname}")
        print(f"filename = {filename}")
        if itemname:
            # filefile = os.path.abspath(os.path.join(self._proj_path, itemspath, itemname, "output", filename))
            # redirect_path = f"/{itemspath}/{itemname}/output/{filename}"
            # http://127.0.0.1:5000/dicts/Google/output/able.html
            # http://127.0.0.1:5000/audios/Google-us/output/able.mp3
            target_filename = f"{itemspath}/{itemname}/output/{filename}"
        else:
            # filefile = os.path.abspath(os.path.join(self._proj_path, itemspath, filename))
            # redirect_path = f"/{itemspath}/{filename}"
            target_filename = f"{itemspath}/{filename}"
        
        normalized_filename = os.path.normpath(target_filename.replace("\\", "/"))
        print(f"normalized_filename = {normalized_filename}")
        # redirect_path = url_for('static', filename=target_filename)
        # pv(redirect_path)
        # print(f"redirect_path = {redirect_path}") 

        full_physical_path = os.path.abspath(
            os.path.join(self._proj_path, normalized_filename)
        )
        print(f"full_physical_path = {full_physical_path}")

        # return redirect(redirect_path)

        dir_name = os.path.dirname(full_physical_path)
        file_name = os.path.basename(full_physical_path)
        # 自动适配MIME类型（Flask会根据文件后缀识别）
        return send_from_directory(
            directory=dir_name,
            path=file_name
        )

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
