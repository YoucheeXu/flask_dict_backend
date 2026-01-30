#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os
import tempfile
from typing import cast

from flask import request, Response, current_app
from flask import jsonify
from flask import send_from_directory
from flask.views import MethodView

from src.logit import pv, po, pe
from src.app.dictapp import DictApp
from src.app_factory import get_dict_app


class FileApi(MethodView):
    """ RESTful style

    """
    def __init__(self):
        self._proj_path: str = cast(str, current_app.static_folder)
        print(f"self._proj_path = {self._proj_path}")
        self._dictapp: DictApp = get_dict_app(self._proj_path)

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

    def post(self, itempath: str, itemnum: int, filename: str) -> tuple[Response, int]:
        """ Handle file upload and process via DictApp.add_file()

        Args:
            itempath: Path parameter from URL (for backward compatibility/organization)
            itemnum: Integer parameter from URL (directly used as dictnum for add_file())
            filename: Target filename from URL (overrides original upload filename)

        Returns:
            Tuple[Response, int]: JSON response with status code:
                - 200: File processed successfully via add_file()
                - 400: Bad request (missing file/invalid dictnum)
                - 500: Server error (add_file() failure or file processing error)

        Tests:
            curl -X POST -F "file=@./German.json"  http://127.0.0.1:5000/dicts/1/upload/German.json
            curl -X POST -F "file=@./German.mp3"  http://127.0.0.1:5000/audios/1/upload/German.mp3
        """
        try:
            # 1. Validate uploaded file presence
            if 'file' not in request.files:
                return jsonify({
                    'code': 400,
                    'msg': 'No file part found in request. Ensure "file" field is included.',
                    'data': None
                }), 400

            upload_file = request.files['file']
            if upload_file.filename == "":
                return jsonify({
                    'code': 400,
                    'msg': 'Uploaded file has empty filename.',
                    'data': None
                }), 400

            # 2. Process filename and save to temporary path (required for add_file())
            file_name = cast(str, filename or upload_file.filename)
            # safe_filename = secure_filename(file_name)  # Sanitize filename for security
            safe_filename = file_name  # Sanitize filename for security

            # Create temporary file (delete after processing; dir = DictApp's proj path)
            # with tempfile.NamedTemporaryFile(
                # delete=False,
                # suffix=os.path.splitext(safe_filename)[1],
                # dir=self._proj_path
            # ) as temp_file:
                # temp_file_path = temp_file.name
                # upload_file.save(temp_file_path)  # Save uploaded file to temp path

            # 3. Create a temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                # 5. Build file path with EXACT target filename (no randomness)
                temp_file_path = os.path.join(temp_dir, safe_filename)

                # 6. Save uploaded file to temp path (exact filename)
                upload_file.save(temp_file_path)

                # 7. Verify file exists (sanity check)
                if not os.path.exists(temp_file_path):
                    return jsonify({
                        'code': 400,
                        'msg': f'Failed to save file to {temp_file_path}',
                        'data': None
                    }), 400

                # 8. Call add_file()
                ret, msg = self._dictapp.add_file(itempath, itemnum, temp_file_path)

                # 9. Clean up temporary file
                # os.unlink(temp_file_path)

                # 10. Return fail response, if fail to add file
                if ret != 1:
                    return jsonify({
                        'code': 400,
                        'msg': msg,
                        'data': None
                    }), 400
                else:
                # 11. Return success response with processing details
                    return jsonify({
                        'code': 200,
                        'msg': msg,
                        'data': {
                            'itempath': itempath,
                            'dictnum': itemnum,
                            'filename': filename
                        }
                    }), 200

        except Exception as e:
            # Catch all exceptions (e.g., add_file() errors, file I/O issues)
            return jsonify({
                'code': 500,
                'msg': f'File processing failed: {str(e)}',
                'data': None
            }), 500

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
