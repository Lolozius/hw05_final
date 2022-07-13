from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

User = get_user_model()


class CreationForm(UserCreationForm):
    """
    Cоздадим собственный класс для формы регистрации.
    Cделаем его наследником предустановленного класса UserCreationForm
    """

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('first_name', 'last_name', 'username', 'email')
