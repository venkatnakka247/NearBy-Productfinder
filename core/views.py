from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from .models import Profile, Shop, Product
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q

# Create your views here.

def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        is_merchant = request.POST.get('is_merchant') == 'on'

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'core/register.html')
        user = User.objects.create_user(username=username, email=email, password=password)
        Profile.objects.create(user=user, is_merchant=is_merchant)
        
        if is_merchant:
            # Auto-login merchant and redirect to shop registration
            login(request, user)
            messages.success(request, 'Merchant registration successful! Now register your shop.')
            return redirect('register_shop')
        else:
            messages.success(request, 'Registration successful. Please log in.')
            return redirect('login')
    return render(request, 'core/register.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            try:
                if user.profile.is_merchant:
                    return redirect('merchant_dashboard')
                else:
                    return redirect('user_dashboard')
            except ObjectDoesNotExist:
                messages.error(request, 'Profile not found.')
                return redirect('login')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'core/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

def merchant_dashboard(request):
    if not request.user.is_authenticated or not hasattr(request.user, 'profile') or not request.user.profile.is_merchant:
        return redirect('login')
    shop = None
    if hasattr(request.user, 'shop_set'):
        shop = request.user.shop_set.first()
    return render(request, 'core/merchant_dashboard.html', {'shop': shop})

def user_dashboard(request):
    if not request.user.is_authenticated or not hasattr(request.user, 'profile') or request.user.profile.is_merchant:
        return redirect('login')
    query = request.GET.get('q', '')
    selected_city = request.GET.get('city', '')
    results = []
    
    if query or selected_city:
        # Start with all products
        products = Product.objects.all()
        
        # Filter by city if selected
        if selected_city:
            products = products.filter(shop__city__iexact=selected_city)
        
        # Filter by product name if query provided
        if query:
            products = products.filter(name__icontains=query)
        
        results = products
    
    return render(request, 'core/user_dashboard.html', {
        'query': query, 
        'selected_city': selected_city,
        'results': results
    })

def register_shop(request):
    if not request.user.is_authenticated or not hasattr(request.user, 'profile') or not request.user.profile.is_merchant:
        return redirect('login')
    if request.method == 'POST':
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        city = request.POST.get('city')
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')
        # Prevent duplicate shop for merchant
        if request.user.shop_set.exists():
            messages.error(request, 'You have already registered a shop.')
            return redirect('merchant_dashboard')
        Shop.objects.create(
            merchant=request.user,
            name=name,
            phone=phone,
            address=address,
            city=city,
            latitude=latitude,
            longitude=longitude
        )
        messages.success(request, 'Shop registered successfully!')
        return redirect('merchant_dashboard')
    return render(request, 'core/register_shop.html')

def add_product(request):
    if not request.user.is_authenticated or not hasattr(request.user, 'profile') or not request.user.profile.is_merchant:
        return redirect('login')
    shop = request.user.shop_set.first()
    if not shop:
        messages.error(request, 'You must register a shop first.')
        return redirect('merchant_dashboard')
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        price = request.POST.get('price')
        image = request.FILES.get('image')
        if not (name and description and price and image):
            messages.error(request, 'All fields are required.')
            return render(request, 'core/add_product.html')
        Product.objects.create(
            shop=shop,
            name=name,
            description=description,
            price=price,
            image=image
        )
        messages.success(request, 'Product added successfully!')
        return redirect('view_products')
    return render(request, 'core/add_product.html')

def view_products(request):
    if not request.user.is_authenticated or not hasattr(request.user, 'profile') or not request.user.profile.is_merchant:
        return redirect('login')
    shop = request.user.shop_set.first()
    if not shop:
        messages.error(request, 'You must register a shop first.')
        return redirect('merchant_dashboard')
    products = shop.product_set.all()
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        if product_id:
            product = products.filter(id=product_id).first()
            if product:
                product.delete()
                messages.success(request, 'Product deleted successfully!')
                return redirect('view_products')
    return render(request, 'core/view_products.html', {'products': products})

def edit_product(request, product_id):
    if not request.user.is_authenticated or not hasattr(request.user, 'profile') or not request.user.profile.is_merchant:
        return redirect('login')
    shop = request.user.shop_set.first()
    if not shop:
        messages.error(request, 'You must register a shop first.')
        return redirect('merchant_dashboard')
    
    product = shop.product_set.filter(id=product_id).first()
    if not product:
        messages.error(request, 'Product not found.')
        return redirect('view_products')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        price = request.POST.get('price')
        image = request.FILES.get('image')
        
        if not (name and description and price):
            messages.error(request, 'Name, description, and price are required.')
            return render(request, 'core/edit_product.html', {'product': product})
        
        # Update product fields
        product.name = name
        product.description = description
        product.price = price
        
        # Update image if new one is provided
        if image:
            product.image = image
        
        product.save()
        messages.success(request, 'Product updated successfully!')
        return redirect('view_products')
    
    return render(request, 'core/edit_product.html', {'product': product})

def home_redirect(request):
    return redirect('login')
