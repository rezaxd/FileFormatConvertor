from __future__ import absolute_import, unicode_literals
from celery import shared_task, Celery
from django.conf import settings
from .models import uploadedFile
from django.core.files import File
import time
import os
import subprocess

def saver(pk, name):
    o_db_f = uploadedFile.objects.get(pk=pk)
    with open(name, 'rb') as f:
        o_db_f.ofile.save(name, File(f, name=name))

@shared_task(bind=True)
def deleter(self, tid):
    try:
        from celery.result import AsyncResult
        AsyncResult(tid).revoke(terminate=True)
    except Exception as exe:
        raise self.retry(exe = exe, max_retries=5)

@shared_task(bind=True)
def imgConvertFunc(self, image_path, name, pk):
    try:
        from PIL import Image
        Image.open(image_path).save(name)
        saver(pk, name)
    except Exception as exe:
        raise self.retry(exe = exe, max_retries=5)
    subprocess.call(['rm', '-r', name])

@shared_task(bind=True)
def musicConvertFucn(self, video_path, name, out_format, pk):
    try:
        from pydub import AudioSegment
        AudioSegment.from_file(video_path).export(name, format=out_format)
        saver(pk, name)
    except Exception as exe:
        raise self.retry(exe = exe, max_retries=5)
    subprocess.call(['rm', '-r', name])