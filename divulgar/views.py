from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.messages import constants
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt

from adotar.models import PedidoAdocao
from usuarios.models import Estado

from .models import Pet, Raca, Tag


@login_required(login_url='login')
def novo_pet(request):
    if request.method == 'GET':
        tags = Tag.objects.all()
        racas = Raca.objects.all()
        estados = Estado.objects.all()
        return render(request, 'novo_pet.html', {'tags': tags, 'racas': racas, 'estados': estados})

    elif request.method == 'POST':
        foto = request.FILES.get('foto')
        nome = request.POST.get('nome').strip()
        descricao = request.POST.get('descricao').strip()
        estado = request.POST.get('estado')
        cidade = request.POST.get('cidade').strip()
        tel = request.POST.get('tel').strip()
        tags = request.POST.getlist('tags')
        raca = request.POST.get('raca')
        sexo = request.POST.get('sexo')

        tel = tel.replace(
            "-", "").replace("(", "").replace(")", "").replace(" ", "")

        pet = Pet(
            usuario=request.user,
            foto=foto,
            nome=nome,
            cidade=cidade,
            estado=estado,
            descricao=descricao,
            tel=tel,
            raca_id=raca,
            sexo=sexo,
        )

        pet.save()

        for tag_id in tags:
            tag = Tag.objects.get(id=tag_id)
            pet.tags.add(tag)

        pet.save()

        return redirect('/divulgar/seus_pets')


@login_required(login_url='login')
def seus_pets(request):
    if request.method == 'GET':
        pets = Pet.objects.filter(usuario=request.user)

        usuario_logado = request.user.first_name

        return render(request, 'seus_pets.html', {'pets': pets, 'usuario_logado': usuario_logado})


@login_required(login_url='login')
def remover_pet(request, id):
    pet = Pet.objects.get(id=id)

    if not pet.usuario == request.user:
        messages.add_message(request, constants.ERROR,
                             'Esse pet não é seu, espertinho hahaha')
        return redirect('/divulgar/seus_pets')

    print(pet)

    pet.delete()

    messages.add_message(request, constants.SUCCESS,
                         'Pet removido com sucesso!')
    return redirect('/divulgar/seus_pets')


@login_required(login_url='login')
def ver_pet(request, id):
    if request.method == 'GET':
        pet = Pet.objects.get(id=id)
        return render(request, 'ver_pet.html', {'pet': pet})


@login_required(login_url='login')
def ver_pedido_adocao(request):
    if request.method == 'GET':
        pedidos = PedidoAdocao.objects.filter(
            pet__usuario=request.user).filter(status='AG')

        if not pedidos:
            messages.add_message(request, constants.INFO,
                                 'Não há nenhum pedido de adoção')

        return render(request, 'ver_pedido_adocao.html', {'pedidos': pedidos})


@login_required(login_url='login')
def perfil_adotante(request, pedido_adocao_id):
    try:
        pedido_adocao = PedidoAdocao.objects.get(id=pedido_adocao_id)
    except Exception as e:
        print(e)
        pass

    usuario_adotante = pedido_adocao.usuario

    return render(request, 'perfil_adotante.html', {'usuario_adotante': usuario_adotante})


@login_required(login_url='login')
def dashboard(request):
    if request.method == 'GET':
        return render(request, 'dashboard.html')


@csrf_exempt
def api_adocoes_por_raca(request):
    racas = Raca.objects.all()

    qtd_adocoes = []
    for raca in racas:
        adocoes = PedidoAdocao.objects.filter(
            pet__raca=raca).filter(status='AP').count()
        qtd_adocoes.append(adocoes)

    racas = [raca.raca for raca in racas]
    data = {
        'qtd_adocoes': qtd_adocoes,
        'labels': racas
    }

    return JsonResponse(data)
