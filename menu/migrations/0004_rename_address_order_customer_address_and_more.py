# Generated by Django 5.2.4 on 2025-07-25 20:49

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('menu', '0003_order_alter_menuitem_image_orderitem'),
    ]

    operations = [
        migrations.RenameField(
            model_name='order',
            old_name='address',
            new_name='customer_address',
        ),
        migrations.RenameField(
            model_name='order',
            old_name='name',
            new_name='customer_name',
        ),
        migrations.RenameField(
            model_name='order',
            old_name='phone',
            new_name='customer_phone',
        ),
        migrations.RemoveField(
            model_name='orderitem',
            name='menu_item',
        ),
        migrations.AddField(
            model_name='orderitem',
            name='menu_item_name',
            field=models.CharField(default='', max_length=100),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='orderitem',
            name='order',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='menu.order'),
        ),
    ]
