from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate
from .serializers import RegistrationSerializer, LoginSerializer, UserInfoSerializer, WalletSerializer, DepositSerializer, TransferSerializer
from rest_framework.views import APIView
from .models import Wallet, CustomUser
from django.db import transaction

class RegistrationView(generics.CreateAPIView):
    serializer_class = RegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)

class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_200_OK)

class UserInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserInfoSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

class WalletInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        wallet = request.user.wallet
        serializer = WalletSerializer(wallet)
        return Response(serializer.data, status=status.HTTP_200_OK)

class DepositView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = DepositSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        amount = serializer.validated_data['amount']
        wallet = request.user.wallet
        wallet.balance += amount
        wallet.save()
        return Response({'message': f'Deposited {amount} successfully.', 'balance': wallet.balance}, status=status.HTTP_200_OK)

class TransferView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        serializer = TransferSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        recipient_wallet_number = serializer.validated_data['recipient_wallet_number']
        amount = serializer.validated_data['amount']
        sender_wallet = request.user.wallet

        if sender_wallet.balance < amount:
            return Response({'error': 'Insufficient balance.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            recipient_wallet = Wallet.objects.select_for_update().get(wallet_number=recipient_wallet_number)
        except Wallet.DoesNotExist:
            return Response({'error': 'Recipient wallet not found.'}, status=status.HTTP_404_NOT_FOUND)

        sender_wallet.balance -= amount
        recipient_wallet.balance += amount
        sender_wallet.save()
        recipient_wallet.save()

        return Response({'message': f'Transferred {amount} to {recipient_wallet_number} successfully.', 'balance': sender_wallet.balance}, status=status.HTTP_200_OK)
