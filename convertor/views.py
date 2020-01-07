from django.views.decorators.http import require_http_methods, require_GET
from .tasks import imgConvertFunc, musicConvertFucn, deleter
from django.http import HttpResponse, HttpResponseRedirect
from django.core.files.storage import FileSystemStorage
from celery_progress.backend import ProgressRecorder
from celery.result import AsyncResult
from django.shortcuts import render
from celery.decorators import task
from django.conf import settings
from .models import uploadedFile
from django.urls import reverse
from celery import shared_task
from pydub import AudioSegment
from PIL import Image
import subprocess
import time
import glob
import os
from django.views.decorators.csrf import csrf_protect


@require_http_methods(["GET", "POST"])
def step1(request):
    if request.method == 'POST':
        upload = uploadedFile()
        uploadedfile = request.FILES["file_up"]
        upload.ifile_name = (uploadedfile.name.replace(' ', '-')).replace('_','-')
        upload.ifile = uploadedfile
        if uploadedfile.size > 104857600:
            error = "'Max File Size': your file is bigger that 100Mg pls split your file into <=100Mg parts!"
            return render(request, "convertor/step1.html", {'error': error})
        upload.size = uploadedfile.size
        out_format = ["png", "png(more format in future!)"] if uploadedfile.name.split('.')[1] == "jpg" else ["mp3", "mpeg"]
        upload.save()
        m1, m2 = "media/%s"%uploadedfile.name.replace(' ', '_'), "media/%s"%(uploadedfile.name.replace(' ', '-')).replace('_','-')
        subprocess.call(['mv', m1, m2])
        return render(request, "convertor/step2.html", {'content': uploadedfile, 'choices': out_format, 'tid': upload.id})
    return render(request, "convertor/step1.html")

@require_http_methods(["GET", "POST"])
def step2(request):
    if request.method == 'POST':
        _f = uploadedFile.objects.get(pk=request.POST['tid'])
        inf = ''
        file_type = 'png'
        file_name = (request.POST['fileName'].replace(' ', '-')).replace('_', '-')
        file_path = "%s/%s"%(os.path.join(settings.BASE_DIR, "media"), file_name)
        out_name = "%s.%s"%(file_name.split(".")[0], file_type)
        _f.ofile_name = out_name
        if file_name.split(".")[1] == 'mp4':
            inf = musicConvertFucn.delay(file_path, out_name, file_type, request.POST['tid'])
            _f.state = inf.state
        else:
            inf = imgConvertFunc.delay(file_path, out_name, request.POST['tid'])
            _f.state = inf.state
        _f.task_id = inf.task_id
        _f.d_url = "%s%s"%(settings.MEDIA_URL, out_name)
        _f.save()
        return render(request, "convertor/step1.html", {'result_name': out_name, 'result_url': "%s%s"%(settings.MEDIA_URL, out_name), 'tid': _f.task_id})

def step3(request):
    content = uploadedFile.objects.all()
    for i in content:
        try:
            i.state = AsyncResult(i.task_id).state
            i.save()
        except:
            i.delete()
    return render(request, "convertor/step3.html", {"content": uploadedFile.objects.all()})

def delete(request, tid):
    deleter.delay(tid)
    return HttpResponseRedirect(reverse('convertor:step3'))
