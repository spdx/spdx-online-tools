# SPDX-FileCopyrightText: 2026-present SPDX Contributors
# SPDX-FileType: SOURCE
# SPDX-License-Identifier: Apache-2.0

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0004_auto_20240102_1751'),
    ]

    operations = [
        migrations.AddField(
            model_name='licenserequest',
            name='github_issue_url',
            field=models.URLField(blank=True, default='', max_length=500),
        ),
        migrations.AddField(
            model_name='licenserequest',
            name='github_issue_number',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
