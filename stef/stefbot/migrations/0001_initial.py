# Generated by Django 4.2.16 on 2025-01-28 10:53

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ModelProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('preview_photo', models.ImageField(upload_to='model_previews/')),
            ],
        ),
        migrations.CreateModel(
            name='TelegramUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('telegram_id', models.BigIntegerField(unique=True)),
                ('username', models.CharField(blank=True, max_length=255, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('pending', 'Ожидает оплаты'), ('paid', 'Оплачено')], default='pending', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('payment_proof', models.TextField(blank=True, null=True)),
                ('model', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='stefbot.modelprofile')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='stefbot.telegramuser')),
            ],
        ),
        migrations.CreateModel(
            name='ModelPhoto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('photo', models.ImageField(upload_to='model_photos/')),
                ('model', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='photos', to='stefbot.modelprofile')),
            ],
        ),
    ]
