from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import *
from .forms import *

# Create your views here.
def index(request):
    products = Product.objects.order_by('-pk')

    context = {
        'products': products,
        # 'image_cnt': products.image_set.count(), # index 페이지에서 carousel로 보여줄 때 사용
    }

    return render(request, 'products/index.html', context)

# admin의 판매 상품 등록
@login_required
def create(request):
    # 요청한 user의 is_superuser가 1이면(admin이면)
    if request.user.is_superuser == 1: 
        if request.method == 'POST':
            product_form = ProductForm(request.POST)
            # form에 image 폼 추가
            image_form = ImageForm(request.POST, request.FILES)
            tmp_images = request.FILES.getlist('image')
            
            # 상품 정보에 대한 폼과 이미지 폼이 유효하면
            if product_form.is_valid() and image_form.is_valid():
                product = product_form.save(commit=False)
                product.admin = request.user

                if tmp_images:
                    for img in tmp_images:
                        img_instance = Image(product=product, image=img)
                        product.save()
                        img_instance.save()

                product.save()
                messages.success(request, '상품 등록이 완료되었습니다.')
                return redirect('products:index')
        else:
            product_form = ProductForm()
            image_form = ImageForm()
            
        context = {
            'product_form': product_form,
            'image_form': image_form,
        }

        return render(request, 'products/create.html', context)
    
    else:
        return redirect('products:index')    # admin 아니면 index로 리다이렉트

def detail(request, product_pk):
    product = Product.objects.get(pk=product_pk)
    inquiry_form = InquiryForm()
    reply_form = ReplyForm()
    inquiries = product.inquiry_set.all()
    replies = product.reply_set.all()

    # model에서 hit은 default=0으로 설정했고 한 번 볼 때마다 1 증가하도록
    product.hit += 1
    product.save()
    
    # 유저 회원가입 시 장바구니가 자동으로 생성됨.
    # 로그인 한 유저면 카트 인스턴스를 생성함.
    if request.user.is_authenticated:
        cart = Cart.objects.get(user=request.user)
    
    # 구매 수량 입력 후 장바구니
    if request.method == 'POST':
        product_buy_form = ProductBuyForm(request.POST)

        if product_buy_form.is_valid():
            form = product_buy_form.save()
            if 'cart' in request.POST:
                CartItem.objects.create(cart=cart, product=product, quantity=form.quantity)

    else:
        product_buy_form = ProductBuyForm()
    
    context = {
        'product': product,
        'image_cnt': product.image_set.count(),
        'product_buy_form': product_buy_form,
        'inquiry_form': inquiry_form,
        'reply_form': reply_form,
        'inquiries': inquiries,
        'replies': replies,
    }

    return render(request, 'products/detail.html', context)

def update(request, product_pk):
    product = Product.objects.get(pk=product_pk)
    images = Image.objects.filter(product_id=product_pk)
    
    # 요청한 user의 is_superuser가 1이면(admin이면)
    if request.user.is_superuser == 1:
        if request.method == 'POST':
            product_form = ProductForm(request.POST, instance=product)
            image_form = ImageForm(request.POST, request.FILES) 
            tmp_images = request.FILES.getlist('image') # TemporaryUploadedFile 객체 리스트

            # 기존 이미지 삭제
            for img in images:
                if img:
                    img.delete()

            # 상품 정보 폼과 이미지 폼이 유효하면
            if product_form.is_valid() and image_form.is_valid():
                product = product_form.save(commit=False)

                if tmp_images:
                    for img in tmp_images:
                        img_instance = Image(product=product, image=img)
                        product.save()
                        img_instance.save()

                product.save()
                # 상품 상세 보기 페이지로
                return redirect('products:detail', product_pk)
        
        else:
            product_form = ProductForm(instance=product)
            if images:
                image_form = ImageForm(instance=images[0])
            else:
                image_form = ImageForm()
            
        context = {
            'product_form': product_form,
            'image_form': image_form,
        }

        return render(request, 'products/create.html', context)
    
    else:
        return redirect('products:detail', product_pk) 

# 찜
def ddib(request, product_pk):
    product = Product.objects.get(pk=product_pk)
    ddib = Ddib.objects.get(user=request.user)

    DdibItem.objects.create(ddib=ddib, product=product)
    
    return redirect('products:detail', product_pk)


# 상품 문의 등록
@login_required
def create_inquiry(request, product_pk):
    product = get_object_or_404(Product, pk=product_pk)
    inquiry_form = InquiryForm(request.POST)    # POST 아닌 건 detail에

    if inquiry_form.is_valid():
        inquiry = inquiry_form.save(commit=False)
        inquiry.user = request.user
        inquiry.product = product
        inquiry.save()

    # 나중에 비동기?

    return redirect('products:detail', product_pk)


@login_required
def create_reply(request, product_pk, inquiry_pk):
    product = get_object_or_404(Product, pk=product_pk)
    inquiry = get_object_or_404(Inquiry, pk=inquiry_pk)
    reply_form = ReplyForm(request.POST)    # POST 아닌 건 detail에

    if request.user.is_superuser == 1:
        if reply_form.is_valid():
            reply = reply_form.save(commit=False)
            reply.user = request.user
            reply.inquiry = inquiry
            reply.product = product
            reply.save()

    # 나중에 비동기

    return redirect('products:detail', product_pk)