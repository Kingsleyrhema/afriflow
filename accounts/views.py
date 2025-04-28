from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate
from .serializers import RegistrationSerializer, LoginSerializer, UserInfoSerializer, WalletSerializer, DepositSerializer, TransferSerializer, TransactionSerializer
from rest_framework.views import APIView
from .models import Wallet, CustomUser, Transaction
from django.db import transaction
from decimal import Decimal
from django.db.models import Q

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

        step = serializer.validated_data.get('step', 'verify')
        recipient_wallet_number = serializer.validated_data['recipient_wallet_number']
        amount = serializer.validated_data['amount']
        description = serializer.validated_data.get('description', '')
        pin = serializer.validated_data.get('pin', None)

        sender_wallet = request.user.wallet

        if step == 'verify':
            try:
                recipient_wallet = Wallet.objects.get(wallet_number=recipient_wallet_number)
                recipient_user = recipient_wallet.user
                return Response({'recipient_name': recipient_user.full_name}, status=status.HTTP_200_OK)
            except Wallet.DoesNotExist:
                return Response({'error': 'Recipient wallet not found.'}, status=status.HTTP_404_NOT_FOUND)

        elif step == 'transfer':
            if pin is None:
                return Response({'error': 'PIN is required to complete the transfer.'}, status=status.HTTP_400_BAD_REQUEST)

            if pin != request.user.pin:
                return Response({'error': 'Invalid PIN.'}, status=status.HTTP_403_FORBIDDEN)

            if sender_wallet.balance < amount:
                return Response({'error': 'Insufficient balance.'}, status=status.HTTP_400_BAD_REQUEST)

            try:
                recipient_wallet = Wallet.objects.select_for_update().get(wallet_number=recipient_wallet_number)
                recipient_user = recipient_wallet.user
            except Wallet.DoesNotExist:
                return Response({'error': 'Recipient wallet not found.'}, status=status.HTTP_404_NOT_FOUND)

            sender_wallet.balance -= amount
            recipient_wallet.balance += amount
            sender_wallet.save()
            recipient_wallet.save()

            Transaction.objects.create(
            sender=request.user,
            receiver=recipient_user,
            amount=amount,
            receiver_name=recipient_user.full_name,
            receiver_account_number=recipient_wallet.wallet_number,
            description=description,
             )

            return Response({
                'message': f'Transferred {amount} to {recipient_user.full_name} ({recipient_wallet_number}) successfully.',
                'balance': sender_wallet.balance,
                'recipient_name': recipient_user.full_name
            }, status=status.HTTP_200_OK)

        else:
            return Response({'error': 'Invalid step parameter.'}, status=status.HTTP_400_BAD_REQUEST)

class TransactionListView(generics.ListAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        transaction_type = self.request.query_params.get('type', None)

        if transaction_type == 'outgoing':
            return Transaction.objects.filter(sender=user).order_by('-timestamp')
        elif transaction_type == 'incoming':
            return Transaction.objects.filter(receiver=user).order_by('-timestamp')
        else:
            # Return all transactions where user is sender or receiver
            return Transaction.objects.filter(Q(sender=user) | Q(receiver=user)).order_by('-timestamp')
        

class TransactionDetailView(generics.RetrieveAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'transaction_id'

    def get_queryset(self):
        user = self.request.user
        return Transaction.objects.filter(Q(sender=user) | Q(receiver=user))
