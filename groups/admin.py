import csv

from django.contrib import admin
from django.contrib.auth.models import User
from django.forms import forms
from django.shortcuts import redirect, render
from django.urls import path
import codecs

from groups.models import ChallengeUser, ChallengeGroup


# Register your models here.

class ImportCSVForm(forms.Form):
    csv_file = forms.FileField()


class ChallengeUserAdmin(admin.ModelAdmin):
    change_list_template = "users_changelist.html"

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('import-csv/', self.import_csv),
        ]
        return my_urls + urls

    def import_csv(self, request):
        if request.method == "POST":
            csv_file = request.FILES["csv_file"]
            reader = csv.reader(codecs.iterdecode(csv_file, 'UTF-8'))
            for row in reader:
                row = [row[i].strip() if row[i] is not None else '' for i in range(10)]
                user_1 = User.objects.create_user(username=row[1],
                                                  password=row[2],
                                                  email=row[2])
                cuser_1 = ChallengeUser(user=user_1,
                                        full_name=row[3],
                                        student_code=row[1])
                cuser_1.save()
                group = ChallengeGroup(name=row[0], owner=cuser_1)
                group.save()
                cuser_1.group = group
                cuser_1.save()
                user_2 = User.objects.create_user(username=row[4],
                                                  password=row[5],
                                                  email=row[5])
                cuser_2 = ChallengeUser(user=user_2,
                                        full_name=row[6],
                                        student_code=row[4],
                                        group=group)
                cuser_2.save()
                if row[7] != '':
                    user_3 = User.objects.create_user(username=row[7],
                                                      password=row[8],
                                                      email=row[8])
                    cuser_3 = ChallengeUser(user=user_3,
                                            full_name=row[9],
                                            student_code=row[7],
                                            group=group)
                    cuser_3.save()
            self.message_user(request, "Your csv file has been imported")
            return redirect("..")
        form = ImportCSVForm()
        payload = {"form": form}
        return render(
            request, "csv_form.html", payload
        )


admin.site.register(ChallengeUser, ChallengeUserAdmin)
