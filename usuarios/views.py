from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.password_validation import validate_password
from django.contrib.messages import constants
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render

from .models import Estado, User, ValidationsUser, Cidade

# Create your views here.


def cadastro(request):
    if request.user.is_authenticated:
        return redirect('/divulgar/novo_pet')
    if request.method == "GET":
        estados = Estado.objects.all()
        cidades_por_estado = {}
        for estado in estados:
            cidades_por_estado[estado.sigla] = Cidade.objects.filter(estado=estado).values_list('nome', flat=True)

        return render(request, 'cadastro.html', {'estados': estados, 'cidades_por_estado': cidades_por_estado})

    elif request.method == "POST":
        usuario = request.POST.get('usuario').strip()
        nome = request.POST.get('nome').strip()
        email = request.POST.get('email').strip()
        senha = request.POST.get('senha').strip()
        confirmar_senha = request.POST.get('confirmar_senha').strip()
        last_name = request.POST.get('last_name').strip()
        tel = request.POST.get('tel').strip()
        estado = request.POST.get('estado')

        if any(len(campo) == 0 for campo in [nome, email, senha, confirmar_senha, last_name, usuario, tel, estado]):
            messages.add_message(request, constants.ERROR,
                                 'Preencha todos os campos!')
            return render(request, 'cadastro.html')

        try:
            validar = ValidationsUser(
                email=email, tel=tel, username=usuario, password=senha, password2=confirmar_senha)

        except ValidationError as e:
            for error in e.messages:
                messages.add_message(request, constants.ERROR, error)
            return render(request, 'cadastro.html')

        try:
            user = User.objects.create_user(
                username=usuario,
                email=email,
                password=senha,
                first_name=nome,
                last_name=last_name,
                tel=tel,
            )
            messages.add_message(request, constants.SUCCESS,
                                 'Seu cadastro foi efetuado!')
            return render(request, 'login.html')

        except:
            messages.add_message(request, constants.ERROR,
                                 'Erro interno do sistema!')
            return render(request, 'cadastro.html')


def logar(request):
    if request.user.is_authenticated:
        return redirect('/adotar/')
    if request.method == 'GET':
        return render(request, 'login.html')
    elif request.method == 'POST':
        usuario = request.POST.get('usuario')
        senha = request.POST.get('senha')
        user = authenticate(username=usuario,
                            password=senha)
        if user is not None:
            login(request, user)
            return redirect('/adotar/')
        else:
            messages.add_message(request, constants.ERROR,
                                 'Usuário ou senha incorretos!')
            return render(request, 'login.html')


def sair(request):
    logout(request)
    return redirect('/auth/login')


def get_nome_estado(estado):
    sigla = estado[0]
    return sigla
