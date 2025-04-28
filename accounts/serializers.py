from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import CustomUser, Wallet, Transaction
import re

class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    pin = serializers.CharField(write_only=True, required=True, max_length=4, min_length=4)
    voice_mode = serializers.BooleanField(required=True)
    enable_biometrics_login = serializers.BooleanField(required=True)

    class Meta:
        model = CustomUser
        fields = ['email', 'password', 'confirm_password', 'business_type', 'full_name', 'phone_number', 'country', 'state_province', 'preferred_language', 'language', 'pin', 'voice_mode', 'enable_biometrics_login']

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        pin = attrs.get('pin')
        if not re.fullmatch(r'\d{4}', str(pin)):
            raise serializers.ValidationError({"pin": "Pin must be exactly 4 digits."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')
        user = CustomUser.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(request=self.context.get('request'), email=email, password=password)
            if not user:
                raise serializers.ValidationError("Unable to log in with provided credentials.")
        else:
            raise serializers.ValidationError("Must include 'email' and 'password'.")
        attrs['user'] = user
        return attrs

class UserInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['email', 'full_name']


class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ['wallet_number', 'balance']

class DepositSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)



class TransferSerializer(serializers.Serializer):
    recipient_wallet_number = serializers.CharField(max_length=6)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    description = serializers.CharField(max_length=255, required=False, allow_blank=True)
    pin = serializers.CharField(max_length=4, required=True, allow_blank=False)
    step = serializers.ChoiceField(choices=['verify', 'transfer'], default='verify')

    
class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['transaction_id', 'sender', 'receiver', 'amount', 'receiver_name', 'receiver_account_number', 'description', 'timestamp', 'transaction_type']
        read_only_fields = ['transaction_id', 'timestamp', 'sender', 'receiver']
