# Generated by Django 3.2.16 on 2022-11-29 14:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='submitlicensemodel',
            name='osiApproved',
            field=models.CharField(choices=[(0, '-'), ('Approved', 'Approved'), ('Not Submitted', 'Not Submitted'), ('Pending', 'Submitted, but pending'), ('Rejected', 'Rejected'), ('Unknown', "Don't know")], default=0, max_length=15),
        ),
        migrations.DeleteModel(
            name='CheckLicenseFileUpload',
        ),
    ]
