import flask
import qldt_schedule_creator
import os
import json
from flask import Flask, request, jsonify
app = Flask(__name__)


@app.route('/api', methods=['GET', 'POST'])
def api():
    msg = request.args.get('last user freeform input')
    rps_text, rps_url = qldt_schedule_creator.main(msg, _GENERATE_IMAGE=True)
    print("IMAGE URL -> {}".format(rps_url))
    # j = {
    #     "messages":[
    #         {"text":rps_text}
    #     ]
    # }
    j = {
        "messages": [
            {"text": rps_text},
            {'attachment': {'type': 'image', 'payload': {'url': rps_url}}}
        ]
    }
    return jsonify(j)


@app.route('/text_api', methods=['GET', 'POST'])
def text_api():
    print(request.form)
    msg = request.form['incoming_message']
    rps_text, rps_url = qldt_schedule_creator.main(msg, _GENERATE_IMAGE=False)
    print("IMAGE URL -> {}".format(rps_url))
    j = {
        "message": rps_text
    }
    print(j)
    return jsonify(j)


@app.route('/image_api', methods=['GET', 'POST'])
def image_api():
    msg = request.args.get('last user freeform input')
    rps_text, rps_url = qldt_schedule_creator.main(msg, _GENERATE_IMAGE=True)
    print("IMAGE URL -> {}".format(rps_url))
    j = {
        "messages": [
            # {"text":rps_text},
            {'attachment': {'type': 'image', 'payload': {'url': rps_url}}}
        ]
    }
    return jsonify(j)


@app.route('/test', methods=['GET'])
def test():
    msg = request.args.get('id')
    rps_text, rps_url = qldt_schedule_creator.main(msg, debug=True)
    print("IMAGE URL -> {}".format(rps_url))
    j = {
        "messages": [
            {"text": rps_text},
            {'attachment': {'type': 'image', 'payload': {'url': rps_url}}}
        ]
    }
    # print(j)
    return jsonify(j)


@app.route('/', methods=['GET', 'POST'])
def index():
    print(request.args)
    return 'hello ^^,'


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, threaded=True)
