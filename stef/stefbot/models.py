from django.db import models


class TelegramUser(models.Model):
    telegram_id = models.BigIntegerField(unique=True)
    username = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username or str(self.telegram_id)


class ModelProfile(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    preview_photo = models.ImageField(upload_to='model_previews/')

    def __str__(self):
        return self.name

class ModelPhoto(models.Model):
    model = models.ForeignKey(ModelProfile, on_delete=models.CASCADE, related_name='photos')
    photo = models.ImageField(upload_to='model_photos/')
   
    def __str__(self):
        return f"Фото для {self.model.name}"
    
class ModelVideo(models.Model):
    model = models.ForeignKey(ModelProfile, on_delete=models.CASCADE, related_name='videos')
    video = models.FileField(upload_to='model_videos/')

    def __str__(self):
        return f"Видео для {self.model.name}"

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидание оплаты'),
        ('paid', 'Оплачено'),
        ('rejected', 'Отклонено')
    ]

    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE)  # Используем TelegramUser
    model = models.ForeignKey(ModelProfile, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_proof = models.ImageField(upload_to='payment_proofs/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Заказ {self.id} - {self.user} - {self.status}"
    
    def set_status_to_paid(self):
        if self.status == 'pending':  # Only update if it's in a pending state
            self.status = 'paid'
            self.save()

    def __str__(self):
        return f"Заказ {self.id} - {self.user} - {self.status}"
