import requests, re, json, time, datetime, pytz, img_uploader, traceback, os, subprocess
from bs4 import BeautifulSoup as bsoup


def init():
	"""
	Initialize global variable and const
	"""
	global r, CAPTCHA_ELEMENT_ID, BROWSER_HEADERS, SUCCESS, GENERATE_IMAGE, FAILURE, home_url, tkb_url, subject_tooltip_pattern, student_id, student_name, student_id_pattern, teacher_id_pattern, date_of_year, img_url
	img_url = None
	date_of_year = '?'
	student_id_pattern = r"[a-zA-Z]{1}[0-9]{2}[a-zA-Z]{4}[0-9]{3}"
	teacher_id_pattern = r"[a-zA-Z]{2}[0-9]{4}"
	subject_tooltip_pattern = r"<td onmouseover=\"ddrivetip\((.*),''.*>"
	SUCCESS = True
	FAILURE = False
	BROWSER_HEADERS = {
		'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36',
		'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
		'Accept-Encoding': 'gzip, deflate',
		'Accept-Language': 'en-US,en;q=0.9,vi;q=0.8,ko;q=0.7',
		'Cache-Control': 'max-age=0',
		'Connection': 'keep-alive',
		'Upgrade-Insecure-Requests': '1'
	}
	r = requests.Session()
	CAPTCHA_ELEMENT_ID = "ctl00_ContentPlaceHolder1_ctl00_lblCapcha"
	home_url = 'http://qldt.ptit.edu.vn/Default.aspx?page=gioithieu'
	tkb_url = 'http://qldt.ptit.edu.vn/Default.aspx?sta=0&page=thoikhoabieu&id='
	return

def get_current_day_of_week():
	tz = pytz.timezone('Asia/Ho_Chi_Minh')
	vn_now = datetime.datetime.now(tz)
	current_hour = int(vn_now.strftime("%H"))
	current_date = vn_now.strftime('%d/%m/%Y')
	current_day_of_week = vn_now.weekday()
	if current_hour < 20:
		# print("van som, bay gio la {}, hien thi lich trong ngay {}".format(current_hour, current_date))
		return current_day_of_week, current_date
	# print("muon roi, {} gio roi, xem lich ngay mai nhe".format(current_hour))
	return (vn_now.weekday()+1)%7, (vn_now + datetime.timedelta(days=1)).strftime('%d/%m/%Y')

def day_of_week_str_to_int(dow):
	dow = dow.lower()
	if dow == "'thứ hai'" or dow == "'monday'":
		return 0
	elif dow == "'thứ ba'" or dow == "'tuesday'":
		return 1
	elif dow == "'thứ tư'" or dow == "'wednesday'":
		return 2
	elif dow == "'thứ năm'" or dow == "'thursday'":
		return 3
	elif dow == "'thứ sáu'" or dow == "'friday'":
		return 4
	elif dow == "'thứ bảy'" or dow == "'saturday'":
		return 5
	elif dow == "'chủ nhật'" or dow == "'sunday'":
		return 6
	else:
		print("KHÔNG THỂ TRANSLATE DAY_OF_WEEK STRING TO INT -> {}".format(dow))
		with open('unicode_dow.txt', 'a+') as f: f.write(dow)
		return -1

def start_time_int_to_hour(n):
	n = int(n[1:-1])
	if n == 1 or n == 3:
		n = n+6
	else:
		n = n+7
	return str(n) + ":00"

def bypass_captcha(rps):
	"""
	This function send bypass captcha requests to server.
	Before this function: global session [r] will be asked for captcha when access qldt.ptit.edu.vn
	After this function: global session [r] has free-access to qldt.ptit.edu.vn.

	Args:
		rps: String object, HTML source code include captcha inside.
	Return:
		true if success
		false if failure
	"""
	global r
	viewstate_pattern = r"id=\"__VIEWSTATE\".*\"(.*)\""
	viewstategenerator_pattern = r"id=\"__VIEWSTATEGENERATOR\".*\"(.*)\""
	CAPTCHA_PATTERN = r"id=\"ctl00_ContentPlaceHolder1_ctl00_lblCapcha\".*?>(.*?)<\/span>"
	viewstate = re.search(viewstate_pattern, rps)
	if viewstate:
		viewstate = viewstate.group(1)
	else:
		print("VIEWSTATE value not found!")
	viewstategenerator = re.search(viewstategenerator_pattern, rps)
	if viewstategenerator:
		viewstategenerator = viewstategenerator.group(1)
	captcha = re.search(CAPTCHA_PATTERN, rps)
	if captcha:
		captcha_text = captcha.group(1)
		print("CAPTCHA -> [{}]".format(captcha_text))
		payload = {
			'ctl00$ContentPlaceHolder1$ctl00$txtCaptcha':captcha_text,
			'__VIEWSTATE':viewstate,
			'__VIEWSTATEGENERATOR':viewstategenerator,
			'__EVENTARGUMENT':'',
			'__EVENTTARGET':'',
			'ctl00$ContentPlaceHolder1$ctl00$btnXacNhan': 'Vào website'
		}
		rps = r.post(url = home_url, headers = BROWSER_HEADERS, data=payload)
		# rps = r.get(home_url)
		if CAPTCHA_ELEMENT_ID not in rps.text:
			print("CAPTCHA BYPASSED")
			return True
		else:
			print("CAPTCHA NOT BYPASSED! PLEASE REPORT TO DEVELOPER BACHVKHOA!")
	else:
		print("CAPTCHA NOT FOUND")
	return False

def init_home_page():
	"""
	If this function SUCCESS, global session [r] could be access qldt.ptit.edu.vn without Captcha asked!

	Return:
		True: if bypass captcha SUCCESS or no-captcha detected
		False: if bypass captcha FAILURE
	"""
	global r
	rps = r.get(home_url, headers = BROWSER_HEADERS)
	# with open('first_get.html', 'w') as f: f.write(rps.text)
	if CAPTCHA_ELEMENT_ID in rps.text:
		# print("CAPTCHA ELEMENT DETECTED!")
		return bypass_captcha(rps.text)
	else:
		print("NO CAPTCHA")
	return True

def get_daily_schedule_from_server_response(tkb_page_html_code):
	"""
	This function get schedule in current day (if exists) in html code provided!

	Args:
		tkb_page_html_code: String object
	"""
	global student_name, date_of_year
	rtn = []
	raw = tkb_page_html_code.decode('utf8')
	subjects = re.findall(subject_tooltip_pattern, raw)
	student_name = re.search(r"id=\"ctl00_ContentPlaceHolder1_ctl00_lblContentTenSV.*>(.*)<\/font>", raw)
	if student_name:
		student_name = student_name.group(1)
		# print("student name -> {}".format(student_name))
	else:
		student_name = "SERVER KHÔNG TRẢ VỀ USERNAME NÀO"
	day_of_week, date_of_year = get_current_day_of_week()
	for subject in subjects:
		subject = subject.split(',')
		# print("lay tkb voi day_of_week = {}, date_of_year = {}".format(day_of_week, date_of_year))
		if day_of_week_str_to_int(subject[3].lower()) == day_of_week:
			sub = [subject[2], subject[1], subject[5], subject[6], subject[8]]
			rtn.append(sub)
	print(subjects)
	return rtn

def find_target_week_in_html_src(html):
	week_pattern = r"value=\"(.*?([0-9\/]{10}).*?([0-9\/]{10})\])"
	week_options = re.findall(week_pattern, html)
	rtn = "NOT FOUND!"
	today = datetime.datetime.now()
	if datetime.datetime.now().weekday() == 6 and datetime.datetime.now().hour >= 20: today += datetime.timedelta(hours = 10)
	for week_option in week_options:
		if datetime.datetime.strptime(week_option[1], '%d/%m/%Y') <= today and today <= datetime.datetime.strptime(week_option[2], '%d/%m/%Y'):
			rtn = week_option[0]
	return rtn

def get_access_to_target_week(student_id):
	"""
	This function get html code of "target" week, target week is the current week of year or the next week of current week of year if current datetime is over 20h Sunday
	"""
	viewstate_pattern = r"id=\"__VIEWSTATE\".*\"(.*)\""
	viewstategenerator_pattern = r"id=\"__VIEWSTATEGENERATOR\".*\"(.*)\""
	week_option_pattern = r"id=\"ctl00_ContentPlaceHolder1_ctl00_ddlTuan\".*\s*.*value=\"(.*)\""
	rps = r.get('http://qldt.ptit.edu.vn/default.aspx?page=thoikhoabieu&sta=0&id='+student_id)
	with open('1430.html', 'wb') as f:
		f.write(rps.content)
	viewstate = re.search(viewstate_pattern, rps.text)
	if viewstate:
		viewstate = viewstate.group(1)
	else:
		print("VIEWSTATE value not found! qldt_schedule_creator 1427")
	viewstategenerator = re.search(viewstategenerator_pattern, rps.text)
	week_option = re.search(week_option_pattern, rps.text).group(1)
	if viewstategenerator:
		viewstategenerator = viewstategenerator.group(1)
	payload = {
		'__VIEWSTATE':viewstate,
		'__VIEWSTATEGENERATOR':viewstategenerator,
		'__EVENTARGUMENT':'',
		'__LASTFOCUS':'',
		'__EVENTTARGET':'ctl00$ContentPlaceHolder1$ctl00$ddlTuan',
		'ctl00$ContentPlaceHolder1$ctl00$ddlChonNHHK':'20182', #this need fixxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
		'ctl00$ContentPlaceHolder1$ctl00$ddlLoai':'0',
		'ctl00$ContentPlaceHolder1$ctl00$ddlTuan':week_option
	}
	rps = r.post(url = 'http://qldt.ptit.edu.vn/default.aspx?page=thoikhoabieu&sta=0&id='+student_id, data = payload)
	rps = r.get(url = 'http://qldt.ptit.edu.vn/default.aspx?page=thoikhoabieu&sta=0&id='+student_id)
	viewstate = re.search(viewstate_pattern, rps.text)
	if viewstate:
		viewstate = viewstate.group(1)
	else:
		print("VIEWSTATE value not found! qldt_schedule_creator 1427")
	viewstategenerator = re.search(viewstategenerator_pattern, rps.text)
	week_option = find_target_week_in_html_src(rps.text)
	if viewstategenerator:
		viewstategenerator = viewstategenerator.group(1)
	payload = {
		'__VIEWSTATE':viewstate,
		'__VIEWSTATEGENERATOR':viewstategenerator,
		'__EVENTARGUMENT':'',
		'__LASTFOCUS':'',
		'__EVENTTARGET':'ctl00$ContentPlaceHolder1$ctl00$ddlTuan',
		'ctl00$ContentPlaceHolder1$ctl00$ddlChonNHHK':'20182', #this need fixxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
		'ctl00$ContentPlaceHolder1$ctl00$ddlLoai':'0',
		'ctl00$ContentPlaceHolder1$ctl00$ddlTuan':week_option
	}
	rps = r.post(url = 'http://qldt.ptit.edu.vn/default.aspx?page=thoikhoabieu&sta=0&id='+student_id, data = payload)
	rps = r.get(url = 'http://qldt.ptit.edu.vn/default.aspx?page=thoikhoabieu&sta=0&id='+student_id)
	with open('1437.html', 'wb') as f:
		f.write(rps.content)
	return rps.content

def qldt_login(username, password):
	global r
	page_name = 'gioithieu'
	viewstate_pattern = r"id=\"__VIEWSTATE\".*\"(.*)\""
	viewstategenerator_pattern = r"id=\"__VIEWSTATEGENERATOR\".*\"(.*)\""
	rps = r.get('http://qldt.ptit.edu.vn/default.aspx?page='+page_name)
	with open('after_first_get.html', 'wb') as f:
		f.write(rps.content)
	viewstate = re.search(viewstate_pattern, rps.text)
	if viewstate:
		viewstate = viewstate.group(1)
	else:
		print("VIEWSTATE value not found! qldt_schedule_creator 1653")
	viewstategenerator = re.search(viewstategenerator_pattern, rps.text)
	if viewstategenerator:
		viewstategenerator = viewstategenerator.group(1)
	payload = {
		'__VIEWSTATE':viewstate,
		'__VIEWSTATEGENERATOR':viewstategenerator,
		'__EVENTARGUMENT':'',
		'ctl00$ContentPlaceHolder1$ctl00$ucDangNhap$txtTaiKhoa':username,
		'ctl00$ContentPlaceHolder1$ctl00$ucDangNhap$txtMatKhau':password,
		'__EVENTTARGET':'',
		'ctl00$ContentPlaceHolder1$ctl00$ucDangNhap$btnDangNhap': 'Đăng Nhập'
	}
	rps = r.post(url = 'http://qldt.ptit.edu.vn/default.aspx?page='+page_name, data=payload)
	rps = r.get('http://qldt.ptit.edu.vn/default.aspx?page='+page_name)
	with open('after_post_payload.html', 'wb') as f: f.write(rps.content)

def get_view_points_source():
	global r
	viewstate_pattern = r"id=\"__VIEWSTATE\".*\"(.*)\""
	viewstategenerator_pattern = r"id=\"__VIEWSTATEGENERATOR\".*\"(.*)\""
	rps = r.get('http://qldt.ptit.edu.vn/default.aspx?page=xemdiemthi')
	with open('1430.html', 'wb') as f:
		f.write(rps.content)
	viewstate = re.search(viewstate_pattern, rps.text)
	if viewstate:
		viewstate = viewstate.group(1)
	else:
		print("VIEWSTATE value not found! qldt_schedule_creator 1637")
	viewstategenerator = re.search(viewstategenerator_pattern, rps.text)
	if viewstategenerator:
		viewstategenerator = viewstategenerator.group(1)
	payload = {
		'__VIEWSTATE':viewstate,
		'__VIEWSTATEGENERATOR':viewstategenerator,
		'__EVENTARGUMENT':'',
		'__LASTFOCUS':'',
		'__EVENTTARGET':'ctl00$ContentPlaceHolder1$ctl00$lnkChangeview2',
		'ctl00$ContentPlaceHolder1$ctl00$txtChonHK':''
	}
	rps = r.post(url = 'http://qldt.ptit.edu.vn/default.aspx?page=xemdiemthi', data=payload)
	with open('1638.html', 'wb') as f: f.write(rps.content)
	return rps
	print("DONE")

def get_all_point_from_html_source(rps):
	soup = bsoup(rps.content, 'lxml')
	points_table = soup.find('div', {'id':'ctl00_ContentPlaceHolder1_ctl00_div1'})
	terms_div = points_table.find_all('tr', {'class':"title-hk-diem"})
	term_lists = []
	for term in terms_div:
		row_diem = term
		term_list_element = []
		term_report = []
		for i in range(0, 40):
			try:
				row_diem = row_diem.find_next('tr')
				if row_diem['class'] == ["row-diem"]:
					tmp_0012 = row_diem.find_all('td')
					tmp_0018 = []
					for item in tmp_0012:
						tmp_0018.append(item.text)
					term_list_element.append(tmp_0018)
					# print(tmp_0018) #tmp_0018 ->['1', 'BAS1141', 'Tiếng anh A11', '3', '0', '0', '0', '0', '100', ' \xa0 ', ' \xa0 ', ' \xa0 ', ' \xa0 ', ' \xa0 ', ' \xa0 ', '10.0', 'A+']
				elif row_diem['class'] == ["row-diemTK"]:
					tmp_0049 = row_diem.find_all('td')
					tmp_0050 = {}
					for item in tmp_0049:
						tmp_0050[item.find_all('span')[0].text] = item.find_all('span')[1].text
					# print(tmp_0050)
					term_report.append(tmp_0050)
				else:
					# print(term_list_element)
					print("{} != {}".format('row-diem', row_diem['class']))
					ten_hk = row_diem.find('td').text
					break
			except:
				pass
		# print(term_list_element)
		# print(term_report)
		j = {}
		j['ten_hk'] = ten_hk
		j['data'] = term_list_element
		j['report'] = term_report
		# print(json.dumps(j, indent=4, sort_keys=True))
		term_lists.append(j)
	# return json.dumps(term_lists)
	return term_lists

def get_weekly_schedule_from_server_response(rps):
	"""
	This function ... hmmm, wrong code convention :((
	"""
	rtn = ""


def schedule_list_to_string(tkb):
	"""
	This function generate response message for webhook from schedule list

	Return: String - reply webhook
	"""
	global student_name, student_id, date_of_year
	course_cnt = len(tkb)
	rtn = "{}, không tìm thấy thời khóa biểu nào tương ứng với mã [{}]\nHọ và tên ->[{}]\n".format(date_of_year, student_id, student_name)
	if course_cnt:
		rtn = "Ngày {}, user {} có {} kíp!\n".format(date_of_year, student_name, course_cnt)
		for index, course in enumerate(tkb):
			rtn += '*****[{}]*****\n{}\n{}\nGV: {}\nThời gian: {}\nĐịa điểm: {}\n'.format(index+1, course[0], course[1], course[4], start_time_int_to_hour(course[3]), course[2])
	rtn += "*****[END]*****\nfrom Bách Văn Khoa's keyboard with love! ;*"
	return rtn

def heroku_generate_image(student_id, cookie_value):
	url = 'http://qldt.ptit.edu.vn/Default.aspx?page=thoikhoabieu&id='
	options = {
		'quality':100,
		'width':2048,
		'crop-h':580,
		'crop-w':1200,
		'crop-x':400,
		'crop-y':250,
		'cookie':[['ASP.NET_SessionId', cookie_value]],
		'user-style-sheet':'inject.css'
	}
	cmd = '/app/bin/wkhtmltoimage '
	for key in options:
		if 'list' in str(type(options[key])):
			l = options[key]
			cmd += '--' + key + ' '
			for pair in l:
				cmd += pair[0] + ' ' + pair[1] + ' '
		else:
			cmd += '--' + str(key) + ' ' + str(options[key]) + ' '
	cmd += "'" + url + student_id + "' "
	timestamp = int(time.time()*10000000)
	outfile =  student_id + '_' + str(timestamp) + '.jpg\''
	cmd += '\'/app/' + outfile
	os.system(cmd)
	# os.system('rm {}'.format(outfile))
	img_url = img_uploader.up(outfile[:-1])
	return img_url

def get_tkb_page(student_id):
	"""
	This function access website with student_id provided and return html source code

	Args:
		student_id: String object
	"""
	global r, img_url
	rtn = r.get(tkb_url + student_id).content
	# head_tag_position = rtn.index('<head>')
	# with open('inject.css', 'r') as f: inject_data = f.read()
	# rtn = rtn[:head_tag_position] + inject_data + rtn[head_tag_position:]
	offline_schedule_file = student_id + '_weekly_' + datetime.datetime.now().strftime('%d-%m-%Y') + '.html'
	with open(offline_schedule_file, 'wb') as f: f.write(rtn)

	# generated_img = student_id + '_weekly_' + datetime.datetime.now().strftime('%H:%m%s %d-%m-%Y')+'.jpg'


	return rtn

def main(msg, _GENERATE_IMAGE):
	global student_id, img_url, GENERATE_IMAGE
	GENERATE_IMAGE = _GENERATE_IMAGE
	init()
	scriptDirectory = os.path.dirname(os.path.realpath(__file__))
	msg = str(msg)
	if re.match(student_id_pattern, msg) or re.match(teacher_id_pattern, msg):
		student_id = msg.upper()
	else:
		return "MA SINH VIEN KHONG HOP LE", None
	print("Nhan duoc yeu cau moi, code  -> {}".format(student_id))
	if init_home_page() == SUCCESS:
		tkb = get_daily_schedule_from_server_response(get_access_to_target_week(student_id))
		rps = schedule_list_to_string(tkb)
	if GENERATE_IMAGE == True: img_url = heroku_generate_image(student_id, r.cookies['ASP.NET_SessionId'])
	return rps, img_url

def get_point_report(username, password):
	print('hello, im get_point_report')
	init()
	if init_home_page() == SUCCESS:
		qldt_login(username, password)
		rps = get_all_point_from_html_source(get_view_points_source())
		return rps

def get_examination_schedule(username, password):
	init()
	if init_home_page() == SUCCESS:
		qldt_login(username, password)
		# rps = get_all_examination_schedule()
		# return rps
	return
def test1():
	global GENERATE_IMAGE
	GENERATE_IMAGE = False
	init()
	if init_home_page() == SUCCESS:
		# qldt_login('b15dccn318', 'bacxiucotdua')
		rps = get_daily_schedule_from_server_response(get_access_to_target_week('B15DCCN318'))
		print(rps)

if __name__ == '__main__':
	# rps = get_point_report('b15dccn318', 'bacxiucotdua')
	# print(rps)
	print(main('b15dccn318', 0))