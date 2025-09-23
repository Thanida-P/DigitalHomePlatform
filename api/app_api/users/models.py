from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager

class UserManager(BaseUserManager):
    def create_user(self, username, password, first_name, last_name):
        if not username:
            raise ValueError('Users must have a username')
        user = self.model(
            username=username,
            first_name=first_name,
            last_name=last_name
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password, first_name, last_name):
        user = self.create_user(username, password, first_name, last_name)
        user.is_admin = True
        user.save(using=self._db)
        return user

class User(AbstractBaseUser):
    username = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    password = models.CharField(max_length=128)  # Django hashes password
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        return self.username

# class Avatar(models.Model):

class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    email = models.EmailField()
    phone_no = models.CharField(max_length=20)
    address = models.JSONField(default=list)
    owned_digital_products = models.JSONField(default=list)
    purchased_history = models.JSONField(default=list)
    credit_cards = models.JSONField(default=list)
    bank_accounts = models.JSONField(default=list)
    cart_id = models.IntegerField(null=True, blank=True)
    
    REQUIRED_FIELDS = ['email', 'phone_no']
