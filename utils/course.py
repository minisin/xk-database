#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json,sys,os
sys.path.append(os.path.abspath(''))
from flask import g, request, session, current_app
from flask import url_for, redirect, abort, flash
import functools
from sqlalchemy.sql import func
from models import Student,Course,Xk,Teacher
import random

def gen_course_table(stuid):
    timetable=[[1 for p in range(7)] for t in range(14)]#14*7
    user = Student.query.get(stuid)
    colors=['red','blue','yellow','green','#00FFFF','black','white','#FE2EF7','#FF8000','#4C0B5F','#A9F5A9','#F7819F']
    random.shuffle(colors)
    count=0
    for i in user.courses:
        count=count+1
        cname=i.desp
        ccode=i.code
        cteaname=''
        for te in i.teacher:
            cteaname+=te.name+' '
        for time in i.ctime:
            timetable[time.starttime-1][time.weekday-1]=[time.durtime,cname,cteaname,ccode,time.place,time.additional,colors[count%(len(colors))]]
            for j in range(time.starttime,time.starttime+time.durtime-1):
                timetable[j][time.weekday-1]=0
    return timetable

def gen_tea_course_table(teaid):
    timetable=[[1 for p in range(7)] for t in range(14)]#14*7
    user = Teacher.query.get(teaid)
    colors=['red','blue','yellow','green','#00FFFF','black','white','#FE2EF7','#FF8000','#4C0B5F','#A9F5A9','#F7819F']
    random.shuffle(colors)
    count=0
    for i in user.courses:
        count=count+1
        cname=i.desp
        ccode=i.code
        cteaname=''
        for te in i.teacher:
            cteaname+=te.name+' '
        for time in i.ctime:
            timetable[time.starttime-1][time.weekday-1]=[time.durtime,cname,cteaname,ccode,time.place,time.additional,colors[count%(len(colors))]]
            for j in range(time.starttime,time.starttime+time.durtime-1):
                timetable[j][time.weekday-1]=0
    return timetable

def transj2w(times):
    tra={'1':u'周一',
         '2':u'周二',
         '3':u'周三',
         '4':u'周四',
         '5':u'周五',
         '6':u'周六',
         '7':u'周日'
    }
    wtime=[]
    for time in times:
        wtime.append("%s %d-%d@%s%s" %(tra[str(time.weekday)],time.starttime,time.durtime+time.starttime-1,time.place,time.additional))
    return '\r\n'.join(wtime)

def transt2line(times):
    tra={'1':u'周一',
         '2':u'周二',
         '3':u'周三',
         '4':u'周四',
         '5':u'周五',
         '6':u'周六',
         '7':u'周日'
    }
    wtime=[]
    for time in times:
        if time.additional is not None and time.additional.replace(' ','')!='':
            wtime.append("%s %d-%d@%s##%s" %(tra[str(time.weekday)],time.starttime,time.durtime+time.starttime-1,time.place,time.additional.replace(' ','')))
        else:
            wtime.append("%s %d-%d@%s" %(tra[str(time.weekday)],time.starttime,time.durtime+time.starttime-1,time.place))
    return ','.join(wtime)

def transline2times(l):
    #解析自然语言描述的日期
    l=l.replace(' ','')
    tra={u'星期':u'周',
         u'周一':'1@',
         u'周二':'2@',
         u'周三':'3@',
         u'周四':'4@',
         u'周五':'5@',
         u'周六':'6@',
         u'周日':'7@',
         u'周末':'7@',
         u'周天':'7@',
    }
    for k,v in tra.items():
        l=l.replace(k,v)
    ts=l.split(',')
    times=[]
    for i in ts:
        if len(i)!=0:
            its=i.split('@')
            if(len(its)!=3):
                return None
            weekday=int(its[0])
            its[1]=its[1].replace(u'到','-')
            tts=its[1].split('-')
            starttime=int(tts[0])
            durtime=int(tts[1])-int(tts[0])+1

            if its[2].find('##')!=-1 and its[2].find('##')!=len(its[2].replace(' ',''))-2:
                nits=its[2].split('##')
                place=nits[0]
                additional=nits[1]
            else:
                place=its[2].replace('##','')
                additional=''
            times.append([weekday,starttime,durtime,place,additional])
    return times

def transline2tea(l):
    k=l.replace(' ','').split(',')
    r=[]
    for i in k:
        if i!='':
            r.append(i)
    return r

def transtea2line(teas):
    wtea=[]
    for tea in teas:
        wtea.append("%s" %tea.teaid)
    return ','.join(wtea)

def check_if_conflict(allc,sc):
    #参数：所有课程列表、待选课程
    #返回：1表示冲突，0表示无冲突
    timetable=[[0 for p in range(7)] for k in range(14)]#14*7
    for lp in allc:
        mk=lp.ctime
        for k in mk:
            for i in range(k.starttime,k.starttime+k.durtime):
                timetable[i-1][k.weekday-1]=1
    mk=sc.ctime
    for k in mk:
        for i in range(k.starttime,k.starttime+k.durtime):
            if timetable[i-1][k.weekday-1]==1:
                return 1
    return 0

def check_if_full(cid):
    #已满=1  可选=0
    num_limit=Course.query.get(cid).num
    num_already=Xk.query.filter(Xk.code==cid).count()
    if num_already>=num_limit:
        return 1
    return 0

def get_credit(sid):
    #学号->学分
    x=Course.session.query(func.sum(Course.credit).label('sum')).join(Xk, Xk.code==Course.code).filter(Xk.stuid==sid)
    return x[0].sum or 0

def get_people_count(cid):
    #类似check_if_full
    num_limit=Course.query.get(cid).num
    num_already=Xk.query.filter(Xk.code==cid).count()
    return {'now':num_already,'max':num_limit}

