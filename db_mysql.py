import mysql.connector
import datetime

class MySQL():
    def __init__(self):
        self.conn = mysql.connector.connect(host="18.191.183.189", user='bvk', passwd='1111', database='mydb')
        self.c = self.conn.cursor()
        self.conn.autocommit = True
    
    def create_examination_schedule(self, j):
        args = [j['student_code'], j['subj_code'], j['subj_name'], j['exam_date'], j['exam_hour'], '0', j['exam_room'], j['exam_type']]
        result = self.c.callproc('create_examination_schedule', args)
        for result in self.c.stored_results():
            print(result.fetchall())

    def check_exam_schedule_notification(self, student_code):
        args = [student_code]
        result = self.c.callproc('get_new_examination_schedule', args)
        exam_schedule = []
        for result in self.c.stored_results():
            results = result.fetchall()
        for result in results:
            j = {}
            j['id'] = result[0]
            j['sub_code'] = result[1]
            j['sub_name'] = result[2]
            j['exam_date'] = result[3].strftime('%d/%m/%Y')
            j['exam_hour'] = result[4]
            j['exam_room'] = result[6]
            j['exam_type'] = result[7]
            exam_schedule.append(j)
        return exam_schedule
    pass
