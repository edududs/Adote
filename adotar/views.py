from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.messages import constants
from django.core.mail import send_mail
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.db.models import Subquery, OuterRef

from divulgar.models import Pet, Raca

from .models import PedidoAdocao


@login_required(login_url='login')
def listar_pets(request):
    if request.method == 'GET':
        pedidos_usuario = PedidoAdocao.objects.filter(usuario=request.user, status="AG").values('pet_id')
        pets = Pet.objects.filter(status='P').exclude(id__in=Subquery(pedidos_usuario))
        racas = Raca.objects.all()

        cidade = request.GET.get('cidade')
        raca_filter = request.GET.get('raca')

        if cidade:
            pets = pets.filter(cidade__icontains=cidade)

        if raca_filter:
            pets = pets.filter(raca__id=raca_filter)
            

            

        return render(request, 'listar_pets.html', {'pets': pets, 'racas': racas, 'cidade': cidade})


@login_required(login_url='login')
def pedido_adocao(request, id_pet):
    pet = Pet.objects.filter(id=id_pet).filter(status='P')

    if not pet.exists():
        messages.add_message(request, constants.WARNING,
                             'Este pet já foi adotado.')
        return redirect('/adotar')
    
    if PedidoAdocao.objects.filter(pet__id=id_pet, usuario=request.user).exists():
        messages.add_message(request, constants.ERROR,
                             'Você já fez um pedido de adoção para este pet!')
        return redirect('/adotar')
    pedido = PedidoAdocao(pet=pet.first(),
                          usuario=request.user,
                          data=datetime.now())
    pedido.save()

    messages.add_message(request, constants.SUCCESS,
                         'Pedido de adoção realizado com sucesso')
    return redirect('/adotar')


def processa_pedido_adocao(request, id_pedido):
    status = request.GET.get('status')
    pedido = PedidoAdocao.objects.get(id=id_pedido)

    if status == 'A':
        pedido.status = 'AP'
        pedido.pet.status = 'A'
        string = '''Olá, sua adoção foi aprovada com sucesso!'''
    elif status == 'R':
        string = '''Olá, sua adoção infelizmente não foi aprovada.'''
        pedido.status = 'R'

    pedido.pet.save()
    pedido.save()

    email = send_mail(
        'Sua adoção foi processada',
        string,
        'dudulj@live.com',
        [pedido.usuario.email,],
    )

    messages.add_message(request, constants.SUCCESS,
                         'Pedido de adoção processado com sucesso!')
    return redirect('/divulgar/ver_pedido_adocao')
