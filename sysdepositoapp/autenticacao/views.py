from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

def index(request):
    # Verifica se o usuário está autenticado
    if request.user.is_authenticated:
        # Se estiver logado, redireciona para a dashboard
        return redirect('dashboard')  # Substitua 'dashboard' pelo nome da sua URL da dashboard
    else:
        # Se não estiver logado, redireciona para a tela de login
        return redirect('login')  # Substitua 'login' pelo nome da sua URL de login

@login_required
def dashboard(request):
    return render(request, 'dashboard.html')


def login_view(request):
    # Se já estiver autenticado, redireciona para dashboard
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        from django.contrib.auth import authenticate, login
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if username and password:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                # Se houver next no GET, redireciona para lá, senão vai para dashboard
                next_url = request.GET.get('next', 'dashboard')
                messages.success(request, f'Bem-vindo(a), {user.username}!')
                return redirect(next_url)
            else:
                messages.error(request, 'Usuário ou senha inválidos.')
        else:
            messages.error(request, 'Por favor, preencha todos os campos.')
    
    return render(request, 'registration/login.html')

def quick_logout(request):
    """Logout rápido sem confirmação"""
    if request.user.is_authenticated:
        username = request.user.username
        logout(request)
        messages.info(request, f'Você saiu do sistema. Até logo, {username}!')
    
    return redirect('/')