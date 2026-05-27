from django.contrib.auth import get_user_model
from rest_framework import serializers


User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    business_group = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email', 'is_active', 'business_group')
        read_only_fields = ('id', 'is_active', 'business_group')

    def get_business_group(self, obj):
        membership = getattr(obj, 'group_membership', None)
        return membership.group.name if membership else None


class CurrentUserSerializer(serializers.ModelSerializer):
    business_group = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'is_active',
            'is_staff',
            'is_superuser',
            'business_group',
        )
        read_only_fields = fields

    def get_business_group(self, obj):
        membership = getattr(obj, 'group_membership', None)
        return membership.group.name if membership else None

