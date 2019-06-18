import flask, qldt_schedule_creator, os, json
from flask import Flask, request, jsonify
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
@app.route('/api', methods=['GET'])
def api():
    msg = request.args.get('last user freeform input')
    rps_text, rps_url = qldt_schedule_creator.main(msg, _GENERATE_IMAGE = True)
    print("IMAGE URL -> {}".format(rps_url))
    j = {
        "messages":[
            {"text":rps_text},
            {'attachment':{'type':'image','payload':{'url':rps_url}}}
        ]
    }
    return jsonify(j)

@app.route('/text_api', methods=['GET'])
def text_api():
    msg = request.args.get('last user freeform input')
    rps_text, rps_url = qldt_schedule_creator.main(msg, _GENERATE_IMAGE = False)
    print("IMAGE URL -> {}".format(rps_url))
    j = {
        "messages":[
            {"text":rps_text}
        ]
    }
    return jsonify(j)

@app.route('/image_api', methods=['GET'])
def image_api():
    msg = request.args.get('last user freeform input')
    rps_text, rps_url = qldt_schedule_creator.main(msg, _GENERATE_IMAGE = True)
    print("IMAGE URL -> {}".format(rps_url))
    j = {
        "messages":[
            {'attachment':{'type':'image','payload':{'url':rps_url}}}
        ]
    }
    return jsonify(j)



@app.route('/test', methods=['GET'])
def test():
    msg = request.args.get('id')
    rps_text, rps_url = qldt_schedule_creator.main(msg, _GENERATE_IMAGE = True)
    print("IMAGE URL -> {}".format(rps_url))
    j = {
        "messages":[
            {"text":rps_text},
            {'attachment':{'type':'image','payload':{'url':rps_url}}}
        ]
    }
    return jsonify(j)


@app.route('/text_api_point_report', methods=['GET'])
def point_report():
    username = request.args.get('username')
    password = request.args.get('password')
    rps_text = qldt_schedule_creator.get_point_report(username, password)
    return jsonify(rps_text)

@app.route('/', methods=['GET'])
def index():
    return 'hello ^^,'
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port = port, threaded=True)
