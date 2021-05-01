import threading
import time
import random
import math
import traceback
import json
import hashlib
import pickle
import os
import datetime
from enum import Enum

import sdk.topos as topos
'''全局变量'''
PROGRAM_LIST = {}
LEGAL_WORDS = ['start', 'stop', 'done', 'reject']
chats = {}   # 记录用户id和chat id的对应
sessions = {}  # 会话池，用于对每个线程登记造册。键名:用户ID, 键值: 字典 (运行程序名program_name, 会话开始时间-秒数时间戳start_time, 会话生命周期-秒数lifetime, 是否进行时间提醒-布尔型timer_notification, 微型数据库memo)
inbox = []  # 收件箱，元素结构：tuple (用户ID, 消息内容)
to_send = []  # 发件箱，元素结构：tuple (用户ID, 消息内容)
lock = threading.Lock()
countryCode = 1
mobile = "1270010000"
password = "ToposBot5678"

'''加载应用列表'''
def reload():
    global PROGRAM_LIST
    with open('apps.json', 'r',encoding="utf-8") as f:
        PROGRAM_LIST = json.load(f)

reload()

'''脚本程序运行线程'''
def run_program(userid, program_name):  # userid是用户ID，program_name是应用名称
    global inbox, to_send, sessions
    FEEDBACKS = ['Good!', 'Nice~', 'Good job!', 'Well done!!', '干得漂亮！', '很好！', '👌']
    rejection_history=[]  #列表中每个元素是一个元组，结构为[(无法完成的指令内容,无法完成的原因)]
    YN = ('是', '否')
    notified_time_points = []
    '''预定义异常'''

    class UserStop(Exception):
        "Exit the thread by throwing an exception"
        def __init__(self):
            say("程序已被成功终止！")

    class ProgramFinished(Exception):
        def __init__(self):
            say("干得漂亮！程序运行结束。程序运行时长：" + sec2hms(time.time()-sessions[userid]['start_time']))

    class TimeLimitExceeded(Exception):
        def __init__(self):
            say("程序运行超过时间限制，已终止。")

    class NotStartedError(Exception):  # 试图在没有使用start函数之前进行其他操作
        def __init__(self):
            say("错误: 程序试图在调用start前使用do, ask或finish。程序已终止。")

    '''时段计次器：统计一段时间内进行了n次某行为'''
    def period_counter(subject:str,d:int,increment:int=0)->int: #查与改合为一体
        initial_date=read_memo("__initial_date_"+subject,datetime.date.today())
        cur_day = datetime.date.today()
        i=0
        start_date=initial_date
        end_date=initial_date+datetime.timedelta(days=d)
        while True:
            if (start_date<=cur_day and cur_day<=end_date):
                break
            else:
                start_date+=datetime.timedelta(days=d)
                end_date+=datetime.timedelta(days=d)
                i+=1
        stat=read_memo("__period_"+ subject + "_" + str(i),0)
        if not increment==0:
            stat+=increment
            super_write_memo("__period_"+subject + "_" + str(i),stat)
            save_data()
        return stat

    def do_sth_every_period(subject:str,d:int):
        if period_counter(subject,d,0)<1:
            if do(subject): period_counter(subject,d,1)

    def unregister():
        lock.acquire()
        if userid in sessions: sessions.pop(userid)
        lock.release()

    def sec2hms(secs):
        s = secs % 60
        m = int(secs / 60) % 60
        h = int(int(secs / 60) / 60) % 60
        rtn = ""
        if h > 0: rtn += "%d小时" % h
        if m > 0: rtn += "%d分钟" % m
        if s > 0: rtn += "%d秒" % s
        return rtn

    # 超时检测方法
    def TLE_check():
        if userid in sessions:
            remaining_time = sessions[userid]['start_time'] + sessions[userid]['lifetime'] - time.time()
            # 先检测是否已经超时
            if remaining_time <= 0:
                raise TimeLimitExceeded
            elif sessions[userid]['timer_notification']:
                # 再发送时间提醒
                time_points = []
                lt = sessions[userid]['lifetime']
                if lt >= 900:  # 15分钟
                    time_points.extend([300, 180, 60])
                if lt >= 1800:  # 30分钟
                    time_points.append(900)
                if lt >= 3600:  # 60分钟
                    time_points.append(1800)
                if lt >= 7200:  # 2小时以上
                    m = math.floor(lt / 3600)
                    for i in range(1, m + 1):
                        if lt > i * 3600 + 900:
                            time_points.append(i * 3600)
                for time_point in time_points:
                    if time_point not in notified_time_points:
                        if abs(remaining_time - time_point) < 5:
                            notified_time_points.append(time_point)
                            say("温馨提示：距离程序结束还有" + sec2hms(time_point))
                            break
        else:
            raise NotStartedError

    def md5encode(data):
        md5=hashlib.md5()
        md5.update(data.encode('utf-8'))
        return md5.hexdigest()

    def save_data():
        f=open('data/' + md5encode(userid+program_name) + ".pickle",'wb')  
        pickle.dump(sessions[userid]["memo"],f,0)  
        f.close()

    def read_memo(prop,default=None):
        try:
            return sessions[userid]["memo"][prop]
        except KeyError:
            return default

    def write_memo(prop,value):
        if not prop[0:2]=="__":   #不允许读取“系统”数据
            sessions[userid]["memo"][prop]=value
            save_data()
            return True
        else:
            return False

    def super_write_memo(prop,value):
        sessions[userid]["memo"][prop]=value
        save_data()
    
    # 脚本可以接触的5个方法：start, do, ask, say, finish, input
    def start(welcome, time_limit=None):
        say(welcome)  # 发送程序欢迎语
        lifetime = 86400  # 默认时间限制为1天。
        timer_notification = False
        msg1 = ""
        if time_limit is not None:
            msg1 = "我们需要在"
            if time_limit[0] > 0:
                msg1 += str(time_limit[0]) + "小时"
            if time_limit[1] > 0:
                msg1 += str(time_limit[1]) + "分钟"
            if time_limit[2] > 0:
                msg1 += str(time_limit[2]) + "秒"
            msg1 += "内走完这个流程~"
            lifetime = time_limit[0] * 3600 + time_limit[1] * 60 + time_limit[2]
            timer_notification = True
        lock.acquire()
        mysession = {}
        mysession['program_name'] = program_name
        mysession['start_time'] = time.time()
        mysession['lifetime'] = lifetime
        mysession['timer_notification'] = timer_notification
        # read pickle data
        filename='data/' + md5encode(userid+program_name) + ".pickle"
        if os.path.exists(filename):
            f=open(filename,'rb')  
            mysession["memo"]=pickle.load(f)  
            f.close()
        else:
            mysession["memo"]={}
        sessions[userid] = mysession  # 创建新会话
        lock.release()
        if timer_notification:
            say("程序已启动，我也开始计时了噢~" + msg1 + "我会在关键时间点提醒你，便于你掌握好节奏。你可以随时输入stop终止程序。")
        else:
            say("程序已启动！你可以随时输入stop终止程序。")

    def say(text):
        topos.send_text(chats[userid], text)

    def input(prompt=None):
        if prompt is not None:
            say(prompt)
        while True:
            TLE_check()
            for msg in inbox:  # 依次查看收件箱中的每条消息
                if msg[0] == userid:  # 如果找到了发给本线程的消息则"打开阅读"
                    inbox.remove(msg)
                    return msg[1]

    def do(message, points=None):
        if userid in sessions:
            msg1 = "现在请" + message + "。\n"
            if points is not None:
                msg1 += "请在完成过程中注意以下要点：\n"
                for p in points:
                    msg1 += "- " + p + "\n"
            msg1 += "做完后请发送done继续；或发送reject告知无法完成。"
            say(msg1)
            while True:
                TLE_check()
                for msg in inbox:  # 依次查看收件箱中的每条消息
                    if msg[0] == userid:  # 如果找到了发给本线程的消息则"打开阅读"
                        inbox.remove(msg)
                        remaining_time = sessions[userid]['start_time'] + sessions[userid]['lifetime'] - time.time()
                        if msg[1] == "done":
                            say(random.choice(FEEDBACKS) + " 现在距离截止时间还有" + sec2hms(remaining_time) + "。")
                            return True
                        elif msg[1] == "stop":
                            raise UserStop
                        elif msg[1] == "reject":
                            reason=input("好吧，解释下无法完成的原因。")
                            rejection_history.append((message,reason))
                            say("好的。现在距离截止时间还有" + sec2hms(remaining_time) + "。")
                            return False
                        else:
                            say('请输入done来继续流程，或输入reject告知无法完成。')
        else:
            raise NotStartedError


    def ask(question, choices=YN):
        if len(choices) < 2: raise ValueError('至少要有2个选项。')
        msg1 = "回答问题：" + question + "\n"
        msg1 += "现有下列答案：\n"
        for choice_id, choice in enumerate(choices, 1):
            msg1 += str(choice_id) + " - " + choice + "\n"
        msg1 += "请发送其中一个数字编号作为对该问题的回答…"
        say(msg1)
        while True:
            TLE_check()
            for msg in inbox:  # 依次查看收件箱中的每条消息
                if msg[0] == userid:  # 如果找到了发给本线程的消息则"打开阅读"
                    inbox.remove(msg)
                    for c in range(1, len(choices)+1):
                        if str(c) == msg[1]:
                            return choices[c-1]
                    if msg[1] == "stop":
                        raise UserStop
                    say('请从答案列表选择并发送一个数字编号。')

    def exit():
        raise ProgramFinished

    ALLOWED_RESOURCES = {"say": say, "start": start, "do": do, "ask": ask, "exit": exit, "input":input, "read_memo":read_memo, "write_memo":write_memo,"period_counter":period_counter,"do_sth_every_period": do_sth_every_period}
    # 在”沙箱“中执行脚本
    try:
        exec(open("apps/" + program_name + ".py",encoding="utf-8").read(), ALLOWED_RESOURCES)
        exit()
    except Exception as e:
        if len(rejection_history)>0:
            str1="===无法完成的原因汇总==="
            for piece in rejection_history:
                str1+="\n" + piece[0] + "无法完成的原因：" + piece[1]
            say(str1)
        print(e)
        traceback.print_exc()
    unregister()


def message_handler(message):
    type: str = message.type
    content: str = message.content
    from_user_id: str = message.from_user_id
    to_chat_id: str = message.to_chat_id
    chats[from_user_id] = to_chat_id  #及时保存UserID-ChatID映射，供其他线程主动发消息使用
    chat: dict = topos.get_chat(chat_id=to_chat_id)
    
    if message.from_user_id is None or message.from_user_id == topos.user.id:
        return

    chat = topos.get_chat(message.to_chat_id)

    # if the message is not a text, do not reply
    if message.type != "text":
        return

    # if the message is from a group chat, do not reply
    if not chat.is_direct:
        return

    # some examples
    if type != "text":
        return topos.send_text(to_chat_id=to_chat_id, content="我目前只能读懂文字哦～")
    user = topos.get_user(user_id=from_user_id)
    nickname = user.nickname    
    # ls 指令列出所有可用程序
    if content == 'ls':
        msg1 = "如需运行某个程序，请发送其对应的指令~"
        for start_command in PROGRAM_LIST.keys():
            msg1 += "\n" + start_command + ": " + PROGRAM_LIST[start_command]
        topos.send_text(to_chat_id, msg1)
    elif content == 'reload':
        reload()
        print("Reloaded")
        topos.send_text(to_chat_id, "Reloaded")
    # 先看看是不是app启动命令
    elif content in PROGRAM_LIST:
        # 某用户启动一程序
        if from_user_id not in sessions:
            print(nickname + "(" + from_user_id + ") has started a program: " + content)  # 控制台提示
            t1 = threading.Thread(target=run_program, args=(from_user_id, content,))
            t1.start()
        else:
            topos.send_text(to_chat_id, "抱歉，程序'" + sessions[from_user_id]['program_name'] + "'已在运行，请先输入stop结束该程序后，再启动新进程。")
    # 如果是合法语言，就把信息放在收件箱里，供线程查阅
    elif from_user_id in sessions:  # 如果用户在执行程序，直接把消息发给程序
        inbox.append((from_user_id, content))
    else:
        topos.send_text(to_chat_id, "'" + content + "' 不是有效的命令或回答，也不是可运行的程序。输入ls查看所有可用程序。")

# bind the message handler
topos.set_message_handler(message_handler=message_handler)

# login the bot user
topos.login(countryCode=countryCode, mobile=mobile,
            password=password)

while True:
    topos.login(countryCode=countryCode, mobile=mobile, password=password)
    time.sleep(600)
