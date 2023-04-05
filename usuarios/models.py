from django.contrib.auth.models import AbstractUser, UserManager
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import models


# Create your models here.
class Estado(models.Model):
    sigla = models.CharField(max_length=2)
    nome = models.CharField(max_length=100)

    def __str__(self):
        return self.nome


class Cidade(models.Model):
    nome = models.CharField(('cidade'), max_length=100)
    estado = models.ForeignKey(Estado, on_delete=models.CASCADE)

    def __str__(self):
        return self.nome


class ValidationsUser:
    def __init__(self, password, password2, email, username, tel):
        self.validate_passwords(password)
        self.email_check_db(email)
        self.username_check_db(username)
        self.tel_check_db(tel)
        self.password_equal_password(password, password2)

    def validate_passwords(self, password):
        validate_password(password)

    def email_check_db(self, email):
        if User.objects.filter(email=email):
            raise ValidationError('Email já cadastrado!')

    def username_check_db(self, username):
        if User.objects.filter(username=username):
            raise ValidationError('Usuário já cadastrado!')

    def tel_check_db(self, tel):
        if User.objects.filter(tel=tel):
            raise ValidationError('Telefone já cadastrado')

    def password_equal_password(self, password1, password2):
        if password1 != password2:
            raise ValidationError(
                'Senhas não conferem, digite duas senhas iguais!')


class User(AbstractUser, UserManager):
    email = models.EmailField(("email adress"), unique=True)
    tel = models.CharField(("phone"), unique=True, max_length=15)

    REQUIRED_FIELDS = ['first_name', 'email', 'tel']

    def __str__(self):
        return self.first_name
