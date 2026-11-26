from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0111_rename_name_cy_contacts_name_kk_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="loginattempt",
            name="username",
            field=models.CharField(blank=True, default="", max_length=254),
        ),
        migrations.AlterField(
            model_name="loginattempt",
            name="user_agent",
            field=models.TextField(blank=True, default=""),
        ),
    ]
