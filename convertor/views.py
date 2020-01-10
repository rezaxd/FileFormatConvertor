from django.views.decorators.http import require_http_methods, require_GET
from .tasks import taskDeleter, imageConvertorFunction, videoConvertorFunction
from django.http import HttpResponse, HttpResponseRedirect
from celery.result import AsyncResult
from django.shortcuts import render
from django.utils import timezone
from django.conf import settings
from .models import uploadedFile
from django.urls import reverse
import subprocess
import os

MAX_UPLOAD_SIZE = 104857600
MAX_UPLOAD_SIZE_ERROR      = "'Max File Size': your file is bigger that 100MG pls split your file into <=100Mg parts!"
FILE_FORMAT_NOT_SUPPORTED  = "'Not Supported format': your file format still is not supported, try upload .mp4 or jpg!"

@require_http_methods(["GET", "POST"])
def step1(request):
    if request.method == 'POST':
        # Create new uploadedFile model instance to save information in db!
        upload = uploadedFile()

        # Set added date:
        upload.addedDate = timezone.now()

        # Store uploaded file from form into uploadedFileFromForm var, and into inputfile in model(db)
        uploadedFileFromForm = request.FILES["file_up"]
        print(uploadedFileFromForm)
        upload.inputFile = uploadedFileFromForm
        
        # Set instance'inputFileName from uploadedFileFromForm.name and replace '_' or ' ' with '-'
        upload.inputFileName = (uploadedFileFromForm.name.replace(' ', '-')).replace('_','-')
        
        # Set instance'size from uploadedFileFromForm.size
        upload.inputFileSize = uploadedFileFromForm.size

        errors =[]
        print(errors)
        # Check for format to be jpg or mp4 except add error in errors list
        if uploadedFileFromForm.name.split('.')[1] != 'jpg' and uploadedFileFromForm.name.split('.')[1] != 'mp4':
            errors.append(FILE_FORMAT_NOT_SUPPORTED)

        # Checking uploadedFileFromForm.size to be lower than MAX_UPLOAD_SIZE
        if uploadedFileFromForm.size > MAX_UPLOAD_SIZE:
            errors.append(MAX_UPLOAD_SIZE_ERROR)
            
        # If any error exists return them into template and break db-save(line 55) operation!
        if errors:            
            return render(request, "convertor/step1.html", {'error': errors})
    
        # Creating a list with available choice for fromat operation
        # if the format of uploadedFileFromForm(or uploaded file) be 'jpg', ['png', 'bmp'] will return as availabe formats in template!
        # else it'll return ['mp3', 'mpeg'] for 'mp4' uploaded file format! so simple!
        out_format = ["png", "bmp"] if uploadedFileFromForm.name.split('.')[1] == "jpg" else ["mp3", "mpeg"]

        # Sotre all information into db!
        upload.save()

        # We'll rename of uploaded file in storage to avoid convert operation problems!
        # _uploadedFile is uploaded file address! and renamedUploadedFile is renamed file name!
        mainUploadedFile, renamedUploadedFile = "media/%s"%uploadedFileFromForm.name.replace(' ', '_'), "media/%s"%(uploadedFileFromForm.name.replace(' ', '-')).replace('_','-')
        subprocess.call(['mv', mainUploadedFile, renamedUploadedFile])
        print(upload.id)
        # Return uploadedFileFromForm.size and name to displayed in next page(selecting output format step)
        # and available choises and id of instance to be used in next view
        return render(request, "convertor/step2.html", {'uploadedFileName': uploadedFileFromForm.name, 'uploadedFileSize': uploadedFileFromForm.size, 'choices': out_format, 'pk': upload.id})

    # If nothing uploaded return main page!
    return render(request, "convertor/step1.html")

@require_http_methods(["GET", "POST"])
def step2(request):
    if request.method == 'POST':
        # Get file from db by id(pk)!
        uploadedFileToChoseOutFormat = uploadedFile.objects.get(pk=request.POST['pk'])
        print(request.POST['fileName'])

        # Define var to store convert result into it, for update state of convert operation into db
        resultFromConvert = ''

        # Get output format from dropdown list in step2.html
        outputFormat = request.POST['fileFormat']
        file_name = (request.POST['fileName'].replace(' ', '-')).replace('_', '-')

        # Create full address of uploded file in storage
        inputFilePath = "%s/%s"%(os.path.join(settings.BASE_DIR, "media"), file_name)

        # Create output file name with specified format & set ouput name in db
        outputName = "%s.%s"%(file_name.split(".")[0], outputFormat)
        uploadedFileToChoseOutFormat.outputFileName = outputName
        
        # if-else to detect file format and run convert function according to output format
        if file_name.split('.')[1] == 'mp4':
            resultFromConvert = videoConvertorFunction.delay(inputFilePath, outputName, outputFormat, request.POST['pk'])
            # update state of operation in db, if code get here the state should be 'PENDING' that means operation started!
            uploadedFileToChoseOutFormat.taskState = resultFromConvert.state
        else:
            resultFromConvert = imageConvertorFunction.delay(inputFilePath, outputName, request.POST['pk'])
            # update state of operation in db, if code get here the state should be 'PENDING' that means operation started!
            uploadedFileToChoseOutFormat.taskState = resultFromConvert.state

        # Store task_id of celery task into db
        uploadedFileToChoseOutFormat.taskId = resultFromConvert.task_id

        # Create Download url for output file
        uploadedFileToChoseOutFormat.downloadUrl = "%s%s"%(settings.MEDIA_URL, outputName)

        # Save all changes into db!
        uploadedFileToChoseOutFormat.save()

        return render(request, "convertor/step1.html")

def step3(request):
    # This function only update the tasks state
    # and returns all record into specified template to display informations
    # information such as state, input file name, output file name and download or cancel button!

    # Get all tasks from db
    convertRequestsRecords = uploadedFile.objects.all()
    
    # Try to update each record(task) state and save that
    # except delete that record, cause in this case of exception file didn't upload!
    for eachConvert in convertRequestsRecords:
        try:
            eachConvert.taskState = AsyncResult(eachConvert.taskId).state
            eachConvert.save()
        except:
            eachConvert.delete()
    return render(request, "convertor/step3.html", {"content": uploadedFile.objects.all()})

def delete(request, task_id):
    # It'll cancel celery task
    taskDeleter.delay(task_id)
    return HttpResponseRedirect(reverse('convertor:step3'))
