from __future__ import absolute_import, unicode_literals
from celery import shared_task
from .models import uploadedFile
from django.core.files import File
import subprocess

def outputFileSaver(pk, name):
    # In this function we'll open output file from covert operation and store it into outputFile in db
    # this function wont run as celery task
    dbRecordToStoreOutpuFile = uploadedFile.objects.get(pk=pk)
    with open(name, 'rb') as f:
        dbRecordToStoreOutpuFile.outputFile.save(name, File(f, name=name))

@shared_task(bind=True)
def taskDeleter(self, tid):
    # This function will revoke or cancel celery task, if any problem occur it'll try 5 times more
    # This function will run as celery task
    try:
        from celery.result import AsyncResult
        AsyncResult(tid).revoke(terminate=True)
    except Exception as exe:
        raise self.retry(exe = exe, max_retries=5)

@shared_task(bind=True)
def imageConvertorFunction(self, image_path, name, pk):
    # Function that Converts file from jpg into png or bmp
    # This function will run as celery task
    try:
        from PIL import Image
        Image.open(image_path).save(name)
        outputFileSaver(pk, name)
    except Exception as exe:
        raise self.retry(exe = exe, max_retries=5)

    # after calling outputFileSaver we'll delete temp file that convert operation created!
    subprocess.call(['rm', '-r', name])

@shared_task(bind=True)
def videoConvertorFunction(self, video_path, name, out_format, pk):
    # Function that converts file from mp4 to mp3 or mpeg!
    # This function will run as celery task
    try:
        from pydub import AudioSegment
        AudioSegment.from_file(video_path).export(name, format=out_format)
        outputFileSaver(pk, name)
    except Exception as exe:
        raise self.retry(exe = exe, max_retries=5)

    # after calling outputFileSaver we'll delete temp file that convert operation created!
    subprocess.call(['rm', '-r', name])