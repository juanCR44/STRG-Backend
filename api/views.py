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

    model = yolov5.load(os.getcwd() + '/SGD640best.pt')
    print(img)
    tobyte = []

    results = model(img)
    detectedImage = Image.fromarray(results.render()[0])
    # results.show()
    size = len(results.pandas().xyxy[0])
    names = []
    average = 0

    for x in range(size):
        left = results.pandas().xyxy[0].xmin[x]
        top = results.pandas().xyxy[0].ymin[x]
        right = results.pandas().xyxy[0].xmax[x]
        bottom = results.pandas().xyxy[0].ymax[x]
        average += results.pandas().xyxy[0].confidence[x]
        names.append(results.pandas().xyxy[0].name[x])

        imgtemp = detectedImage
        imgcrop = imgtemp.crop((left, top, right, bottom))
        tobyte.append(imgcrop)

    result = []
    buffered = BytesIO()

    detectedImage.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue())
    img_base64 = bytes("data:image/jpeg;base64,", encoding='utf-8') + img_str
    final = img_base64.decode('UTF-8')

    result.append(final)

    for x in range(len(tobyte)):
        buffered = BytesIO()
        tobyte[x].save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue())
        img_base64 = bytes("data:image/jpeg;base64,",
                           encoding='utf-8') + img_str
        finalcrop = img_base64.decode('UTF-8')
        result.append(finalcrop)

    if len(result) > 1:
        average = average / (len(result) - 1)

    return result, round(average, 2), names


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
    #im = Image.open(os.getcwd() + '/IMG_PRODUCTS_VAL826.png')
    result, average, names = doYolo(im)

    print(average, len(result)-1, ' nani')
    return JsonResponse(
        {
            'imagearr': result,
            'count': len(result) - 1,
            'average': average,
            'names': names
        }, safe=False)


def doYoloState(img):
    model = yolov5.load(os.getcwd() + '/SGD640best.pt')
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
        mySql_insert_query = """INSERT INTO DetectionResult (user_id, count, percentage, date, namestate, imagestate, percentagestate, state)
                               VALUES
                               (%s, %s, %s, %s, %s, %s, %s, %s) """

        record = (data['user_id'], data['count'], data['percentage'], datetime.datetime.now(), data['namestate'], data['imagestate'], data['percentagestate'], data['state'])
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
        sql_select_query = """select * from DetectionResult where user_id = %s and date = %s and namestate = %s"""

        record = (data['user_id'], data['date'], data['producttype'])
        cursor.execute(sql_select_query, record)

        res = dictfetchall(cursor)

        if len(res) < 1:
            return JsonResponse({'error': 'ERROR'}, safe=False)
        else:
            #res = {'id': result[0][0], 'email': result[0][1], 'enterprise': result[0][3]}
            return JsonResponse(
                { 
                    'data': json.dumps(res, default=str)
                    #json.dumps({'data': res.decode('utf-8')})
                }, safe=False)

    except mysql.connector.Error as error:
        return JsonResponse({'error': 'ERROR'}, safe=False)