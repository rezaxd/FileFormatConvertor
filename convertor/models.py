from django.db import models

class uploadedFile(models.Model):
    ifile_name = models.CharField(null=False, blank=False, max_length=100)
    ifile = models.FileField(null=True, max_length=100)
    size = models.CharField(null=True, max_length=50)
    ofile_name = models.CharField(null=True, max_length=100)
    ofile = models.FileField(null=True, max_length=100)
    state = models.CharField(null=True, max_length=50)
    task_id = models.CharField(null=True, max_length=50)
    d_url = models.CharField(null=True, max_length=200)

    def __str__(self):
        return self.ifile_name
    