#!/usr/bin/python3
# -*- coding: utf-8 -*-
from flask import request, Response, redirect, url_for
from flask.views import MethodView

from src.logit import pv, po, pe


class FileApi(MethodView):
    """ RESTful style

    """
    def __init__(self):
        pass

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
            # redirect_path = f"/public/{itemspath}/{itemname}/output/{filename}"
            redirect_path = url_for('static', filename=f"/{itemspath}/{itemname}/output/{filename}")
        else:
            # filefile = os.path.abspath(os.path.join(self._proj_path, itemspath, filename))
            # redirect_path = f"/public/{itemspath}/{filename}"
            redirect_path = url_for('static', filename=f"/{itemspath}/{filename}")
        
        # print(f'filefile = {filefile}')
        pv(redirect_path)
        print(f'redirect_path = {redirect_path}')

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
