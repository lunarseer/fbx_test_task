import os
import re


from flask import Flask, jsonify, send_from_directory, json



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
    if os.path.exists(os.path.join(FILESDIRECTORY, path)):
        return send_from_directory(FILESDIRECTORY, path, as_attachment=True)
    return app.response_class(
                              response=json.dumps({'message': 'Not Found'}),
                              status=404,
                              mimetype='application/json'
                              )
