from rest_framework import serializers
from .models import TelegramUser, ModelProfile, ModelPhoto, Order

class TelegramUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelegramUser
        fields = ['id', 'telegram_id', 'username', 'created_at']

class ModelProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelProfile
        fields = ['id', 'name', 'description', 'price', 'preview_photo']

class ModelPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelPhoto
        fields = ['id', 'model', 'photo']

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['id', 'user', 'model', 'status', 'created_at', 'payment_proof']
