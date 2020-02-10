import requests
import re
import json
import time
import datetime
import pytz
import traceback


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
    return (vn_now.weekday()+1) % 7, (vn_now + datetime.timedelta(days=1)).strftime('%d/%m/%Y')


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
        with open('unicode_dow.txt', 'a+') as f:
            f.write(dow)
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
            'ctl00$ContentPlaceHolder1$ctl00$txtCaptcha': captcha_text,
            '__VIEWSTATE': viewstate,
            '__VIEWSTATEGENERATOR': viewstategenerator,
            '__EVENTARGUMENT': '',
            '__EVENTTARGET': '',
            'ctl00$ContentPlaceHolder1$ctl00$btnXacNhan': 'Vào website'
        }
        rps = r.post(url=home_url, headers=BROWSER_HEADERS, data=payload)
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
    If this function SUCCESS, global session [r] will be access qldt.ptit.edu.vn without Captcha asked!

    Return:
        True: if bypass captcha SUCCESS or no-captcha detected
        False: if bypass captcha FAILURE
    """
    global r
    rps = r.get(home_url, headers=BROWSER_HEADERS)
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
    raw = tkb_page_html_code
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
    # print(rtn)
    return rtn


def schedule_list_to_string(tkb):
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
        'quality': 100,
        'width': 2048,
        'crop-h': 580,
        'crop-w': 1200,
        'crop-x': 400,
        'crop-y': 250,
        'cookie': [['ASP.NET_SessionId', cookie_value]],
        'user-style-sheet': 'inject.css'
    }
    cmd = 'bin\\wkhtmltoimage '
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
    outfile = student_id + '_' + str(timestamp) + '.jpg\''
    cmd += '\'/app/' + outfile
    print('generate img command -> [{}]'.format(cmd))
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
    rtn = r.get(tkb_url + student_id).text
    # head_tag_position = rtn.index('<head>')
    # with open('inject.css', 'r') as f: inject_data = f.read()
    # rtn = rtn[:head_tag_position] + inject_data + rtn[head_tag_position:]
    offline_schedule_file = student_id + '_weekly_' + datetime.datetime.now().strftime('%d-%m-%Y') + '.html'
    with open(offline_schedule_file, 'w', encoding='utf-8') as f:
        f.write(rtn)

    # generated_img = student_id + '_weekly_' + datetime.datetime.now().strftime('%H:%m%s %d-%m-%Y')+'.jpg'

    img_url = heroku_generate_image(student_id, r.cookies['ASP.NET_SessionId']) if GENERATE_IMAGE == True else None
    return rtn


def main(msg, _GENERATE_IMAGE=False):
    global student_id, img_url, GENERATE_IMAGE
    GENERATE_IMAGE = _GENERATE_IMAGE
    init()
    msg = str(msg)
    if re.match(student_id_pattern, msg) or re.match(teacher_id_pattern, msg):
        student_id = msg.upper()
    else:
        return "MA SINH VIEN KHONG HOP LE", None
    print("Nhan duoc yeu cau moi, code  -> {}".format(student_id))
    if init_home_page() == SUCCESS:
        tkb = get_daily_schedule_from_server_response(get_tkb_page(student_id))
        rps = schedule_list_to_string(tkb)
    return rps, img_url
