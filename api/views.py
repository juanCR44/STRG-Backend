from django.shortcuts import render
from django.http import JsonResponse
import json
from PIL import Image
from io import BytesIO
import base64
import os
import torch

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
    model = torch.hub.load('ultralytics/yolov5', 'yolov5s')
    #model = torch.hub.load('ultralytics/yolov5', 'custom', path='static/yolov5s.pt', force_reload=True).autoshape()
    #ROOT_DIR = os.getcwd()
    tobyte = []

    print('2')

    results = model(img)
    detectedImage = Image.fromarray(results.render()[0])
    # results.show()
    size = len(results.pandas().xyxy[0])

    print('3')

    for x in range(size):
        left = results.pandas().xyxy[0].xmin[x]
        top = results.pandas().xyxy[0].ymin[x]
        right = results.pandas().xyxy[0].xmax[x]
        bottom = results.pandas().xyxy[0].ymax[x]

        imgtemp = detectedImage
        imgcrop = imgtemp.crop((left, top, right, bottom))
        tobyte.append(imgcrop)

    result = []
    buffered = BytesIO()

    print('4')

    detectedImage.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue())
    img_base64 = bytes("data:image/jpeg;base64,", encoding='utf-8') + img_str
    final = img_base64.decode('UTF-8')
    
    print('5')

    result.append(final)

    for x in range(len(tobyte)):
        buffered = BytesIO()
        tobyte[x].save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue())
        img_base64 = bytes("data:image/jpeg;base64,",
                           encoding='utf-8') + img_str
        finalcrop = img_base64.decode('UTF-8')
        result.append(finalcrop)

    print('6')

    return result
    ##print(ROOT_DIR + '/weight/SGD640best.pt')
    #model = torch.load(ROOT_DIR + '/api/weight/SGD640best.pt')
    # print(ROOT_DIR)
    # print(model)


@api_view(['POST'])
def testYolo(request):
    data = request.data
    data = json.dumps(data)
    data = json.loads(data)
    # print(data['image'])

    imgb64 = data['image'].split('data:image/jpeg;base64,')[1]

    # print(data)
    im = Image.open(BytesIO(base64.b64decode(imgb64)))
    # print(im)
    result = doYolo(im)
    #print(result)
    #print(len(result))
    print(result)

    return JsonResponse({'data': result}, safe=False)
