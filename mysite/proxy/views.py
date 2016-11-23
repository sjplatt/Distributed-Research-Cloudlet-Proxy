from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.
def getCache(request):
    return HttpResponse("Hello World, you are in getCache.")

def callBack(request):
    return HttpResponse("Hello World, you are in callBack.")