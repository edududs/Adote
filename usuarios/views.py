from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.messages import constants
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render

from .models import Estado, User, ValidationsUser

# Create your views here.


def cadastro(request):
    if request.user.is_authenticated:
        return redirect('/divulgar/novo_pet')
    if request.method == "GET":
        estados = Estado.objects.all()
        return render(request, 'cadastro.html', {'estados': estados})

    elif request.method == "POST":
        estados = Estado.objects.all()

        usuario = request.POST.get('usuario').strip()
        nome = request.POST.get('nome').strip()
        email = request.POST.get('email').strip()
        senha = request.POST.get('senha').strip()
        confirmar_senha = request.POST.get('confirmar_senha').strip()
        last_name = request.POST.get('last_name').strip()
        descricao = request.POST.get('descricao')
        tel = request.POST.get('tel').strip()
        cep = request.POST.get('cep').strip()
        bairro = request.POST.get('bairro').strip()
        cidade = request.POST.get('cidade').strip()
        uf = request.POST.get('estado')
        uf = Estado.objects.get(nome=uf)

        cep = cep.replace("-", "").replace(" ", "").replace(".", "")
        tel = tel.replace(
            "-", "").replace("(", "").replace(")", "").replace(" ", "")
        print(
            f"cep: {cep}\ntel:{tel}\nbairro:{bairro}\ncidade:{cidade}\nuf:{uf}")
        
        if usuario == "admin":
                user = User.objects.create_superuser(
                    username=usuario,
                    email=email,
                    password=senha,
                    first_name=nome,
                    last_name=last_name,
                    tel=tel,
                    cep=cep,
                    bairro=bairro,
                    cidade=cidade,
                    uf=uf,
                    descricao=descricao,
                )
                messages.add_message(request, constants.SUCCESS,
                                 'Seu cadastro foi efetuado!')
                return render(request, 'login.html')
        if not uf:
            messages.add_message(request, constants.ERROR,
                                 'Estado não encontrado.')
            return render(request, 'cadastro.html', {'estados': estados})

        if any(len(campo) == 0 for campo in [nome, email, senha, confirmar_senha, usuario, tel, descricao]):
            messages.add_message(request, constants.ERROR,
                                 'Preencha todos os campos obrigatórios!')
            return render(request, 'cadastro.html', {'estados': estados})

        try:
            validar = ValidationsUser(
                email=email, tel=tel, username=usuario, password=senha, password2=confirmar_senha)

        except ValidationError as e:
            for error in e.messages:
                messages.add_message(request, constants.ERROR, error)
            return render(request, 'cadastro.html', {'estados': estados})

        try:
            user = User.objects.create_user(
                username=usuario,
                email=email,
                password=senha,
                first_name=nome,
                last_name=last_name,
                tel=tel,
                cep=cep,
                bairro=bairro,
                cidade=cidade,
                uf=uf,
                descricao=descricao
            )
            messages.add_message(request, constants.SUCCESS,
                                 'Seu cadastro foi efetuado!')
            return render(request, 'login.html')

        except Exception as e:
            print(e)
            messages.add_message(request, constants.ERROR,
                                 'Erro interno do sistema!')
            return render(request, 'cadastro.html', {'estados': estados})


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


def perfil(request):
    if request.method != 'POST':
        username = request.user.first_name + " " + request.user.last_name
        return render(request, 'perfil.html', {'username': username})


def sair(request):
    logout(request)
    return redirect('/auth/login')
