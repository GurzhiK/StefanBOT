from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TelegramUserViewSet, ModelProfileViewSet, ModelPhotoViewSet, OrderViewSet
from .views import create_order

router = DefaultRouter()
router.register(r'users', TelegramUserViewSet)
router.register(r'models', ModelProfileViewSet)
router.register(r'model-photos', ModelPhotoViewSet)
router.register(r'orders', OrderViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    path('create_order/', create_order, name='create_order'),
]
