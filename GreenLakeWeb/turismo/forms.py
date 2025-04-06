from django import forms
from .models import Usuario

class CambiarRolForm(forms.ModelForm):
    tipo_usuario = forms.ChoiceField(choices=Usuario.TIPO_USUARIO_CHOICES, label="Nuevo rol")

    class Meta:
        model = Usuario
        fields = ['tipo_usuario']
