from django.shortcuts import render
from django.http import HttpResponse
import json
import netifaces as ni
import dateutil.parser
import datetime
import requests
from django.views.decorators.csrf import csrf_exempt
import redis
ni.ifaddresses('eth0')

cache = redis.StrictRedis(host='localhost', port=6379, db=0)

# Returns the datetime parameter from params
def removeDateTime(params):
    if params is None:
        return None
    else:
        res = []
        for temp in params:
            if not isinstance(temp, datetime.datetime):
                res += [temp]

        return tuple(res)

@csrf_exempt
def callBack(request):
    body = request.body.split("|")
    sql, params = body[0], None

    if len(body) == 2:
        params = removeDateTime(eval(body[1]))

    key = str(sql)
    if not params is None:
        key = str(sql) + "|" + str(params)

    if cache.get(key):
        print "Callback remove key"
        cache.delete(key)

    return HttpResponse("Hello World, you are in callBack.")