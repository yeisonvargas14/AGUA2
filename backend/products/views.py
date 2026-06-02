from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from core.decorators import role_required
from .models import Product
from promotions.models import Promotion
from ratings.models import Rating
from django.db.models import Q, Avg
from decimal import Decimal

@login_required
@role_required('client')
def catalogo_view(request):
    query = request.GET.get('q', '')
    products = Product.objects.filter(is_active=True)
    
    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )
    
    # Calculate average rating for each product and attach active promotions
    for prod in products:
        prod.avg_rating = prod.ratings.aggregate(Avg('score'))['score__avg'] or 0.0
        # Check active promotion
        promo = prod.promotions.filter(is_active=True).first()
        if promo and promo.is_current:
            prod.discounted_price = prod.price * (Decimal('1') - Decimal(promo.discount_percentage) / Decimal('100'))
            prod.promo = promo
        else:
            prod.discounted_price = prod.price
            prod.promo = None

    return render(request, 'client/catalogo.html', {
        'products': products,
        'query': query
    })

@login_required
@role_required('client')
def product_detail_view(request, pk):
    product = get_object_or_404(Product, pk=pk, is_active=True)
    
    # Check promotions
    promo = product.promotions.filter(is_active=True).first()
    if promo and promo.is_current:
        product.discounted_price = product.price * (Decimal('1') - Decimal(promo.discount_percentage) / Decimal('100'))
        product.promo = promo
    else:
        product.discounted_price = product.price
        product.promo = None

    # Get product ratings
    ratings = Rating.objects.filter(product=product).order_by('-created_at')
    avg_rating = ratings.aggregate(Avg('score'))['score__avg'] or 0.0
    
    return render(request, 'client/detalle.html', {
        'product': product,
        'ratings': ratings,
        'avg_rating': avg_rating
    })

def landing_page(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    query = request.GET.get('q', '')
    products = Product.objects.filter(is_active=True)
    
    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )
    
    # Calculate average rating and apply active promotions for landing page
    for prod in products:
        prod.avg_rating = prod.ratings.aggregate(Avg('score'))['score__avg'] or 0.0
        promo = prod.promotions.filter(is_active=True).first()
        if promo and promo.is_current:
            prod.discounted_price = prod.price * (Decimal('1') - Decimal(promo.discount_percentage) / Decimal('100'))
            prod.promo = promo
        else:
            prod.discounted_price = prod.price
            prod.promo = None

    return render(request, 'landing.html', {
        'products': products,
        'query': query
    })
