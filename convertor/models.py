from django.db import models

class uploadedFile(models.Model):
    inputFileName = models.CharField(null=False, blank=False, max_length=100)
    inputFile = models.FileField(null=True, max_length=100)
    inputFileSize = models.CharField(null=True, max_length=50)
    outputFileName = models.CharField(null=True, max_length=100)
    outputFile = models.FileField(null=True, max_length=100)
    taskState = models.CharField(null=True, max_length=50)
    taskId = models.CharField(null=True, max_length=50)
    downloadUrl = models.CharField(null=True, max_length=200)
    addedDate = models.DateTimeField("Date uploaded!")

    def __str__(self):
        return self.inputFileName