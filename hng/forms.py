from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth import get_user_model


User = get_user_model()

class UserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('email','first_name','last_name','phone')


class UserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ('email',)
