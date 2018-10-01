from django.contrib import admin

from main.models import (Jedi, Planet, Order, Question, Challenge)

admin.site.register(Jedi)
admin.site.register(Planet)
admin.site.register(Order)
admin.site.register(Question)
admin.site.register(Challenge)
