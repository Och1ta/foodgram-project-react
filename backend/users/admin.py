from django.contrib import admin

from users.models import Follow, User


class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'username', 'first_name', 'last_name', 'password')
    list_filter = ('email', 'username')


class FollowAdmin(admin.ModelAdmin):
    list_display = ('user', 'following')


admin.site.register(User, UserAdmin)
admin.site.register(Follow, FollowAdmin)
