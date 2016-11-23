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

# Helper methods

def customDeserializeDatetime(obj):
    try:
        if "datetime" in str(obj):
            return dateutil.parser.parse(obj.split(":")[1])
        else:
            return obj
    except:
        return obj

def customSerializeDatetime(obj):
    if isinstance(obj, datetime.datetime):
        return "datetime:" + obj.isoformat()
    raise TypeError("Type not serializable Boo")

def convertToValue(data, rc, error, ret):
    return json.dumps([ret, data, rc, error], default=customSerializeDatetime)

def removeDateTimeFromKey(key):
    if not "datetime" in str(key):
        return key

    body = key.split("|")
    query, params = body[0], None
    if len(body) == 2:
        params = json.loads(body[1], object_pairs_hook=customDeserializeDatetime)
        params = [p for p in params if not "datetime" in str(p)]

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

def convertToKey(sql, params):
    if params is None:
        return str(sql)
    elif not "datetime" in str(params):
        return str(sql) + "|" + str(params)
    else:
        return str(sql) + "|" + json.dumps(params, default=customSerializeDatetime)

def putInCache(sql, params, data, rc, error):
    params = removeDateTime(params)

    if not "SELECT" in str(sql):
        return

    if params is None:
        key = str(sql)
        cache.set(key, json.dumps([data, rc, str(error)], default=customSerializeDatetime))
    else:
        key = str(sql) + "|" + str(params)
        cache.set(key, json.dumps([data, rc, str(error)], default=customSerializeDatetime))

def sendQueryToCloud(sql, params):
    params = json.dumps(params, default=customSerializeDatetime)
    key = str(sql) + "|" + params
    ip = ni.ifaddresses('eth0')[2][0]['addr']
    # Send the request to the cloud and get the response
    r = requests.post("http://54.213.170.131:8000/polls/", data=key, headers={"source":ip})
    ret, data, rc, error = json.loads(r.text)
    
    data = [customDeserializeDatetime(d) for d in data]

    return ret, data, rc, error

def lookupCache(sql, params):
    params = removeDateTime(params)
    if params is None:
        value = cache.get(str(sql))
        if value:
            values = json.loads(value)
            
            mydata = [customDeserializeDatetime(v) for v in values[0]]
            rc = values[1]
            error = True
            if values[2] == "False":
                error = False
            
            return mydata, rc, error, None
        else:
            return False
    else:
        value = cache.get(str(sql) + "|" + str(params))
        if value:
            values = json.loads(value)
            
            mydata = [customDeserializeDatetime(v) for v in values[0]]
            rc = values[1]
            error = True
            if values[2] == "False":
                error = False

            return mydata, rc, error, None
        else:
            return False

@csrf_exempt
def getCache(request):
    body = request.body.split("|")
    sql, params = body[0], None

    if len(body) == 2:
        params = json.loads(body[1], object_pairs_hook=customDeserializeDatetime)
        if not params is None:
            params = [customDeserializeDatetime(p) for p in params]

    # If the element is in the cache return None
    if lookupCache(sql, params):
        # print("HIT")
        val, rc, error, ret = lookupCache(sql, params)
        return HttpResponse(convertToValue(val, rc, error, ret))
    else:
        print("MISS")
        ret, val, rc, error = sendQueryToCloud(sql,params)

        # Only add to the cache if ret is not null
        if ret == None:
            putInCache(sql, params, val, rc, error)
        
        return HttpResponse(convertToValue(val, rc, error, ret))

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