"""
Serializers for authentication app.
"""
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import User, UserProfile, APIKey
from .utils import verify_wallet_signature
import re


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT token serializer with additional user data.
    """
    
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Add custom claims
        data['user'] = {
            'id': str(self.user.id),
            'email': self.user.email,
            'username': self.user.username,
            'is_verified': getattr(self.user.profile, 'is_verified', False),
            'wallet_address': getattr(self.user.profile, 'wallet_address', None),
        }
        
        return data


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    """
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    wallet_address = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = User
        fields = ('email', 'username', 'password', 'password_confirm', 'first_name', 'last_name', 'wallet_address')
    
    def validate_email(self, value):
        """Validate email uniqueness."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value
    
    def validate_username(self, value):
        """Validate username uniqueness."""
        if value and User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value
    
    def validate_wallet_address(self, value):
        """Validate Ethereum wallet address format."""
        if value:
            if not re.match(r'^0x[a-fA-F0-9]{40}$', value):
                raise serializers.ValidationError("Invalid Ethereum wallet address format.")
            
            # Check if wallet address is already linked to another user
            if UserProfile.objects.filter(wallet_address=value).exists():
                raise serializers.ValidationError("This wallet address is already linked to another account.")
        
        return value
    
    def validate(self, attrs):
        """Validate password confirmation."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords do not match.")
        return attrs
    
    def create(self, validated_data):
        """Create user with profile."""
        wallet_address = validated_data.pop('wallet_address', None)
        validated_data.pop('password_confirm')
        
        # Create user
        user = User.objects.create_user(**validated_data)
        
        # Update profile with wallet address if provided
        if wallet_address:
            user.profile.wallet_address = wallet_address
            user.profile.save()
        
        return user


class WalletAuthSerializer(serializers.Serializer):
    """
    Serializer for wallet-based authentication.
    """
    wallet_address = serializers.CharField(max_length=42)
    signature = serializers.CharField()
    nonce = serializers.CharField()
    
    def validate_wallet_address(self, value):
        """Validate Ethereum wallet address format."""
        if not re.match(r'^0x[a-fA-F0-9]{40}$', value):
            raise serializers.ValidationError("Invalid Ethereum wallet address format.")
        return value.lower()  # Normalize to lowercase
    
    def validate(self, attrs):
        """Verify wallet signature."""
        wallet_address = attrs['wallet_address']
        signature = attrs['signature']
        nonce = attrs['nonce']
        
        # Verify the signature
        if not verify_wallet_signature(wallet_address, nonce, signature):
            raise serializers.ValidationError("Invalid signature.")
        
        return attrs


class WalletConnectSerializer(serializers.Serializer):
    """
    Serializer for wallet connection (nonce generation).
    """
    wallet_address = serializers.CharField(max_length=42)
    
    def validate_wallet_address(self, value):
        """Validate Ethereum wallet address format."""
        if not re.match(r'^0x[a-fA-F0-9]{40}$', value):
            raise serializers.ValidationError("Invalid Ethereum wallet address format.")
        return value.lower()


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile.
    """
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    user_first_name = serializers.CharField(source='user.first_name')
    user_last_name = serializers.CharField(source='user.last_name')
    
    class Meta:
        model = UserProfile
        fields = (
            'user_email', 'user_username', 'user_first_name', 'user_last_name',
            'wallet_address', 'bio', 'avatar', 'website', 'location',
            'verification_status', 'reputation_score', 'total_datasets_uploaded',
            'total_datasets_purchased', 'total_earnings', 'total_spent',
            'email_notifications', 'marketing_emails', 'created_at', 'updated_at'
        )
        read_only_fields = (
            'verification_status', 'reputation_score', 'total_datasets_uploaded',
            'total_datasets_purchased', 'total_earnings', 'total_spent',
            'created_at', 'updated_at'
        )
    
    def validate_wallet_address(self, value):
        """Validate wallet address."""
        if value:
            if not re.match(r'^0x[a-fA-F0-9]{40}$', value):
                raise serializers.ValidationError("Invalid Ethereum wallet address format.")
            
            # Check if wallet address is already linked to another user
            current_user = self.instance.user if self.instance else None
            existing_profile = UserProfile.objects.filter(wallet_address=value).first()
            
            if existing_profile and existing_profile.user != current_user:
                raise serializers.ValidationError("This wallet address is already linked to another account.")
        
        return value
    
    def update(self, instance, validated_data):
        """Update user and profile data."""
        # Extract user data
        user_data = {}
        for field in ['user_first_name', 'user_last_name']:
            if field in validated_data:
                user_field = field.replace('user_', '')
                user_data[user_field] = validated_data.pop(field)
        
        # Update user fields
        if user_data:
            for field, value in user_data.items():
                setattr(instance.user, field, value)
            instance.user.save()
        
        # Update profile fields
        for field, value in validated_data.items():
            setattr(instance, field, value)
        
        instance.save()
        return instance


class APIKeySerializer(serializers.ModelSerializer):
    """
    Serializer for API keys.
    """
    key = serializers.CharField(read_only=True)
    
    class Meta:
        model = APIKey
        fields = (
            'id', 'name', 'key', 'is_active', 'can_read', 'can_write', 'can_delete',
            'last_used', 'usage_count', 'created_at', 'expires_at'
        )
        read_only_fields = ('key', 'last_used', 'usage_count', 'created_at')
    
    def create(self, validated_data):
        """Create API key with generated key."""
        from core.utils import generate_api_key
        
        validated_data['key'] = generate_api_key()
        validated_data['user'] = self.context['request'].user
        
        return super().create(validated_data)


class PasswordChangeSerializer(serializers.Serializer):
    """
    Serializer for password change.
    """
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(required=True)
    
    def validate_old_password(self, value):
        """Validate old password."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value
    
    def validate(self, attrs):
        """Validate password confirmation."""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("New passwords do not match.")
        return attrs
    
    def save(self):
        """Change user password."""
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Serializer for password reset request.
    """
    email = serializers.EmailField()
    
    def validate_email(self, value):
        """Validate email exists."""
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("No user found with this email address.")
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer for password reset confirmation.
    """
    token = serializers.CharField()
    new_password = serializers.CharField(validators=[validate_password])
    new_password_confirm = serializers.CharField()
    
    def validate(self, attrs):
        """Validate password confirmation."""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("Passwords do not match.")
        return attrs


class UserSerializer(serializers.ModelSerializer):
    """
    Basic user serializer.
    """
    profile = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 'is_verified', 'created_at', 'profile')
        read_only_fields = ('id', 'is_verified', 'created_at')
