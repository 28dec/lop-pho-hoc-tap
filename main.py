import flask, qldt_schedule_creator, os, json, mysql.connector
import db_mysql
from flask import Flask, request, jsonify
app = Flask(__name__)
# db = db_mysql.MySQL()
app.config['JSON_AS_ASCII'] = False
@app.route('/api', methods=['GET'])
def api():
	msg = request.args.get('last user freeform input')
	rps_text, rps_url = qldt_schedule_creator.main(msg, _GENERATE_IMAGE = False)
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

@app.route('/text_api_view_examination_schedule', methods=['GET'])
def examination_schedule():
	username = request.args.get('username')
	password = request.args.get('password')
	rps = qldt_schedule_creator.get_examination_schedule_source(username, password)
	return jsonify(rps)

@app.route('/text_api_qldt_check_login', methods=['GET'])
def check_login():
	username = request.args.get('username')
	password = request.args.get('password')
	rps = qldt_schedule_creator.qldt_check_login(username, password)
	j = {}
	j['result'] = rps
	return jsonify(j)


# @app.route('/text_api_check_exam_schedule_notification', methods=['GET'])
# def check_exam_schedule_notification():
# 	global db
# 	username = request.args.get('username')
# 	password = request.args.get('password')
# 	# qldt_schedule_creator.get_examination_schedule_source(username, password) # sai code convention, get_exam_schedule cung add cac exam vao db luon, nen moi goi ham nay o day
# 	rps = db.check_exam_schedule_notification(username)
# 	return jsonify(rps)

@app.route('/', methods=['GET'])
def index():
	return 'hello ^^,'
if __name__ == '__main__':
	port = int(os.environ.get('PORT', 5000))
	app.run(host='0.0.0.0', port = port, threaded=True)
