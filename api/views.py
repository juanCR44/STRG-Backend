from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.db import connection
import mysql.connector
import json
from PIL import Image
from io import BytesIO
import base64
import os
import torch
import yolov5
import random
from .models import User
import datetime

from rest_framework.decorators import api_view
from rest_framework.response import Response

# Create your views here.


@api_view(['GET'])
def apiOverView(request):

    print("jee")
    # api_urls = {
    #    'list':'/task-list/',
    #    'create':'/task-create/'
    # }

    return JsonResponse({'data': 'bien'}, safe=False)


def doYolo(img):
    print('1')
    # model = torch.hub.load('ultralytics/yolov5', 'yolov5s')
    # model = torch.load(os.getcwd() + '/yolov5s.pt')
    # torch.hub.set_dir(os.getcwd())
    # model = torch.hub.load('ultralytics/yolov5', 'custom', path=os.getcwd() + '/yolov5s.pt',trust_repo=True, source='local')
    # model = torch.hub.load(os.getcwd()+'/ultralytics_yolov5_master', 'custom', path= os.getcwd() + '/yolov5s.pt', source='local', skip_validation=True)

    model = yolov5.load(os.getcwd() + '/best_sgd_640.pt')
    print(img)

    results = model(img)
    detectedImage = Image.fromarray(results.render()[0])
    # results.show()
    size = len(results.pandas().xyxy[0])

    resultGood = []
    resultBad = []

    tobyteGood = []
    tobyteBad = []
    namesGood = []
    namesBad = []

    names = []
    average = 0

    for x in range(size):
        average += results.pandas().xyxy[0].confidence[x]
        if average < 0.85:
            continue

        left = results.pandas().xyxy[0].xmin[x]
        top = results.pandas().xyxy[0].ymin[x]
        right = results.pandas().xyxy[0].xmax[x]
        bottom = results.pandas().xyxy[0].ymax[x]
        
        imgtemp = detectedImage
        imgcrop = imgtemp.crop((left, top, right, bottom))

        if results.pandas().xyxy[0].name[x].split('ME')[0] == '':
            namesBad.append(results.pandas().xyxy[0].name[x])
            tobyteBad.append(imgcrop)
        else:
            namesGood.append(results.pandas().xyxy[0].name[x])
            tobyteGood.append(imgcrop)

    buffered = BytesIO()

    detectedImage.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue())
    img_base64 = bytes("data:image/jpeg;base64,", encoding='utf-8') + img_str
    final = img_base64.decode('UTF-8')

    resultGood.append(final)

    for x in range(len(tobyteGood)):
        buffered = BytesIO()
        tobyteGood[x].save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue())
        img_base64 = bytes("data:image/jpeg;base64,",
                           encoding='utf-8') + img_str
        finalcrop = img_base64.decode('UTF-8')
        resultGood.append(finalcrop)

    for x in range(len(tobyteBad)):
        buffered = BytesIO()
        tobyteBad[x].save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue())
        img_base64 = bytes("data:image/jpeg;base64,",
                           encoding='utf-8') + img_str
        finalcrop = img_base64.decode('UTF-8')
        resultBad.append(finalcrop)

    if len(resultGood) > 1 or len(resultBad) > 0:
        average = average / ((len(resultGood) - 1) + len(resultBad))

    return resultGood, resultBad,round(average, 2), namesGood, namesBad


@api_view(['POST'])
def detect(request):
    data = request.data

    data = json.dumps(data)
    data = json.loads(data)

    if data['image'].split('/')[1].split(';')[0] == 'jpeg':
        imgb64 = data['image'].split('data:image/jpeg;base64,')[1]
    if data['image'].split('/')[1].split(';')[0] == 'png':
        imgb64 = data['image'].split('data:image/png;base64,')[1]
    im = Image.open(BytesIO(base64.b64decode(imgb64)))
    #im = Image.open(os.getcwd() + '/image.jpg')
    resultGood, resultBad,average, namesGood, namesBad = doYolo(im)

    print(average, namesGood, namesBad)
    return JsonResponse(
        {
            'resultGood': resultGood,
            'resultBad': resultBad,
            'count': (len(resultGood) - 1) + len(resultBad),
            'average': average,
            'namesGood': namesGood,
            'namesBad': namesBad
        }, safe=False)


def doYoloState(img):
    model = yolov5.load(os.getcwd() + '/temp.pt')
    results = model(img)
    #detectedImage = Image.fromarray(results.render()[0])

    average = results.pandas().xyxy[0].confidence[0]

    arr = ['Bueno', 'Malo']
    val = random.randint(0, 1)
    state = arr[val]

    #buffered = BytesIO()
    #detectedImage.save(buffered, format="JPEG")
    #img_str = base64.b64encode(buffered.getvalue())
    #img_base64 = bytes("data:image/jpeg;base64,", encoding='utf-8') + img_str
    #final = img_base64.decode('UTF-8')

    return round(average, 2), state


@api_view(['POST'])
def detectState(request):
    data = request.data

    data = json.dumps(data)
    data = json.loads(data)

    imgb64 = data['image'].split('data:image/jpeg;base64,')[1]
    im = Image.open(BytesIO(base64.b64decode(imgb64)))

    average, state = doYoloState(im)

    return JsonResponse(
        {
            'average': average,
            'state': state
        }, safe=False)


@api_view(['POST'])
def registerUser(request):
    try:
        data = request.data
        print(data['email'])

        cursor = connection.cursor()
        mySql_insert_query = """INSERT INTO User (email, password, enterprise)
                               VALUES
                               (%s, %s, %s) """

        record = (data['email'], data['password'], data['enterprise'])
        cursor.execute(mySql_insert_query, record)

        connection.commit()

        return HttpResponse(status=201)
    except mysql.connector.Error as error:
        return HttpResponse(status=500)

@api_view(['POST'])
def registerDetection(request):
    try:
        data = request.data
        cursor = connection.cursor()
        mySql_insert_query = """INSERT INTO DetectionResult (user_id, count, percentage, date, names, nametype,images)
                               VALUES
                               (%s, %s, %s, %s, %s, %s, %s) """

        record = (data['user_id'], data['count'], data['percentage'], datetime.datetime.now(),  data['names'], data['nametype'],data['images'])
        cursor.execute(mySql_insert_query, record)

        connection.commit()

        return HttpResponse(status=201)
    except mysql.connector.Error as error:
        return HttpResponse(status=500)

@api_view(['POST'])
def loginUser(request):
    try:
        data = request.data
        cursor = connection.cursor()
        sql_select_query = """select * from User where email = %s and password = %s"""
        # set variable in query
        record = (data['email'], data['password'])
        cursor.execute(sql_select_query, record)

        print(data)

        result = cursor.fetchall()

        print(result[0][0])

        if len(result) < 1:
            return JsonResponse({'error': 'ERROR'}, safe=False)
        else:
            res = {'id': result[0][0], 'email': result[0][1], 'enterprise': result[0][3]}
            return JsonResponse(
                {
                    'data': res
                }, safe=False)

    except mysql.connector.Error as error:
        return JsonResponse({'error': 'ERROR'}, safe=False)

def dictfetchall(cursor):
    "Return all rows from a cursor as a dict"
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]

@api_view(['POST'])
def getDetection(request):
    try:
        data = request.data

        cursor = connection.cursor()
        sql_select_query = """select * from DetectionResult where user_id = %s and date = %s and nametype = %s"""
        record = (data['user_id'], data['date'], data['producttype'])
        cursor.execute(sql_select_query, record)
        res = dictfetchall(cursor)
        
        ##res2 = []
        ##if data['producttype'] == 'IncaKola_1.5L':
        ##    sql_select_query2 = """select * from DetectionResult where user_id = %s and date = %s and nametype = %s"""
        ##    record2 = (data['user_id'], data['date'], 'ME_IncaKola_1.5L')
        ##    cursor.execute(sql_select_query2, record2)
        ##    res2 = dictfetchall(cursor)
        ##elif data['producttype'] == 'SanMateo_2.5L':
        ##    sql_select_query2 = """select * from DetectionResult where user_id = %s and date = %s and nametype = %s"""
        ##    record2 = (data['user_id'], data['date'], 'ME_SanMateo_2.5L')
        ##    cursor.execute(sql_select_query2, record2)
        ##    res2 = dictfetchall(cursor)
        ##elif data['producttype'] == 'Cielo_2.5L':
        ##    sql_select_query2 = """select * from DetectionResult where user_id = %s and date = %s and nametype = %s"""
        ##    record2 = (data['user_id'], data['date'], 'ME_Cielo_2.5L')
        ##    cursor.execute(sql_select_query2, record2)
        ##    res2 = dictfetchall(cursor)
        ##elif data['producttype'] == 'MonsterOriginal_473ml':
        ##    sql_select_query2 = """select * from DetectionResult where user_id = %s and date = %s and nametype = %s"""
        ##    record2 = (data['user_id'], data['date'], 'ME_MonsterOriginal_473ml')
        ##    cursor.execute(sql_select_query2, record2)
        ##    res2 = dictfetchall(cursor)
        ##elif data['producttype'] == 'MonsterZeroSugar_473ml':
        ##    sql_select_query2 = """select * from DetectionResult where user_id = %s and date = %s and nametype = %s"""
        ##    record2 = (data['user_id'], data['date'], 'ME_MonsterZeroSugar_473ml')
        ##    cursor.execute(sql_select_query2, record2)
        ##    res2 = dictfetchall(cursor)
        ##elif data['producttype'] == 'RedBull_250ml':
        ##    sql_select_query2 = """select * from DetectionResult where user_id = %s and date = %s and nametype = %s"""
        ##    record2 = (data['user_id'], data['date'], 'ME_RedBull_250ml')
        ##    cursor.execute(sql_select_query2, record2)
        ##    res2 = dictfetchall(cursor)
##
        ##if len(res2)>0:
        ##    totallist = res + res2
        ##else:
        ##    totallist = res

        totallist = res

        if len(res) < 1:
            return JsonResponse({'error': 'ERROR'}, safe=False)
        else:
            #res = {'id': result[0][0], 'email': result[0][1], 'enterprise': result[0][3]}
            return JsonResponse(
                { 
                    'data': json.dumps(totallist, default=str)
                    #json.dumps({'data': res.decode('utf-8')})
                }, safe=False)

    except mysql.connector.Error as error:
        return JsonResponse({'error': 'ERROR'}, safe=False)