import os
import re


from flask import Flask, request, abort, jsonify, send_from_directory



ROOTDIRECTORY = os.path.dirname(os.path.abspath(__file__))

FILESDIRECTORY = os.path.join(ROOTDIRECTORY, 'files')


app = Flask('filestorage')


@app.route("/files")
def list_files():
    """
    files list endpoint
    """
    def iszip(name):
        return re.match('.*.zip$', name)
    files = [x for x in os.listdir(FILESDIRECTORY) if iszip(x)]
    return jsonify(files)


@app.route("/files/<path:path>")
def get_file(path):
    """
    file download endpoint
    """
    return send_from_directory(FILESDIRECTORY, path, as_attachment=True)