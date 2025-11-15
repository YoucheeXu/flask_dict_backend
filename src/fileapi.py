#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys
import os
import json

from flask import request, Response, redirect
from flask.views import MethodView

from logit import pv


class FileApi(MethodView):
    '''
        RESTful style
    '''
    def __init__(self):
        # self._proj_path: str = proj_path
        exe_path = os.path.dirname(os.path.abspath(__file__))
        if getattr(sys, "frozen", False):
            exe_path = os.path.dirname(os.path.abspath(sys.executable))
        self._proj_path: str = os.path.join(exe_path, "..", "public")

    def get(self, itemspath: str, itemname: str = "", filepath: str = ""):
        '''
            query
        '''
        pv(itemspath)
        pv(itemname)
        pv(filepath)
        if itemname:
            filefile = os.path.join(self._proj_path, itemspath, itemname, "output", filepath)
            pv(os.path.abspath(filefile))
            redirect_path = f"/public/{itemspath}/{itemname}/output/{filepath}"
        else:
            filefile = os.path.join(self._proj_path, itemspath, filepath)
            pv(os.path.abspath(filefile))
            redirect_path = f"/public/{itemspath}/{filepath}"

        # with open(filefile, 'rb') as f:
            # fileas = f.read()
            # resp = Response(fileas, mimetype='application/octet-stream            
        return redirect(redirect_path)

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
