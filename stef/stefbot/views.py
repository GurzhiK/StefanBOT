from rest_framework import viewsets
from .models import TelegramUser, ModelProfile, ModelPhoto, Order
from .serializers import TelegramUserSerializer, ModelProfileSerializer, ModelPhotoSerializer, OrderSerializer
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from .models import ModelProfile, Order, TelegramUser
from django.contrib.auth.models import User
import json

class TelegramUserViewSet(viewsets.ModelViewSet):
    queryset = TelegramUser.objects.all()
    serializer_class = TelegramUserSerializer

class ModelProfileViewSet(viewsets.ModelViewSet):
    queryset = ModelProfile.objects.all()
    serializer_class = ModelProfileSerializer

class ModelPhotoViewSet(viewsets.ModelViewSet):
    queryset = ModelPhoto.objects.all()
    serializer_class = ModelPhotoSerializer

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

def create_order(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        telegram_id = data.get('telegram_id')
        model_id = data.get('model_id')

        user, created = TelegramUser.objects.get_or_create(telegram_id=telegram_id)

        model = get_object_or_404(ModelProfile, id=model_id)
        amount = model.price

        order = Order.objects.create(user=user, model=model, amount=amount)

        return JsonResponse({'order_id': order.id, 'status': order.status})