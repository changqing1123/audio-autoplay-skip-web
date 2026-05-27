from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.core.validators import FileExtensionValidator

from .models import GroupProfile, ManagedGroup, ManagedUser, UserGroupMembership, validate_group_cover_size


User = get_user_model()


class ManagedUserCreationForm(forms.ModelForm):
    business_group = forms.ModelChoiceField(
        label='所属分组',
        queryset=ManagedGroup.objects.order_by('name'),
        required=False,
        empty_label='未选择分组',
    )
    password = forms.CharField(
        label='密码',
        required=False,
        strip=False,
        widget=forms.PasswordInput(render_value=True),
        help_text='留空时使用系统默认密码。',
    )

    class Meta:
        model = ManagedUser
        fields = (
            'username',
            'password',
            'business_group',
        )

    def save(self, commit=True):
        user = super().save(commit=False)
        raw_password = self.cleaned_data.get('password') or self._get_default_password()
        user.is_active = True
        user.is_staff = False
        user.is_superuser = False
        user.set_password(raw_password)
        if commit:
            user.save()
            self._save_group_membership(user)
        return user

    def _get_default_password(self):
        business_group = self.cleaned_data.get('business_group')
        if business_group:
            profile, _ = GroupProfile.objects.get_or_create(
                group=business_group,
                defaults={'default_password': settings.ADMIN_DEFAULT_PASSWORD},
            )
            if profile.default_password:
                return profile.default_password
        return settings.ADMIN_DEFAULT_PASSWORD

    def _save_group_membership(self, user):
        business_group = self.cleaned_data.get('business_group')
        if business_group:
            UserGroupMembership.objects.update_or_create(
                user=user,
                defaults={'group': business_group},
            )
        else:
            UserGroupMembership.objects.filter(user=user).delete()


class ManagedUserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField(label='Password')
    business_group = forms.ModelChoiceField(
        label='所属分组',
        queryset=ManagedGroup.objects.order_by('name'),
        required=False,
        empty_label='未选择分组',
    )
    reset_password_to_default = forms.BooleanField(
        label='重置为默认密码',
        required=False,
    )
    new_password = forms.CharField(
        label='新密码',
        required=False,
        strip=False,
        widget=forms.PasswordInput(render_value=True),
    )

    class Meta:
        model = ManagedUser
        fields = (
            'username',
            'password',
            'new_password',
            'reset_password_to_default',
            'business_group',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        membership = getattr(self.instance, 'group_membership', None)
        if membership:
            self.fields['business_group'].initial = membership.group_id

    def clean_password(self):
        return self.initial.get('password')

    def save(self, commit=True):
        user = super().save(commit=False)
        new_password = self.cleaned_data.get('new_password')
        reset_to_default = self.cleaned_data.get('reset_password_to_default')
        if new_password:
            user.set_password(new_password)
        elif reset_to_default:
            user.set_password(self._get_default_password())
        if commit:
            user.save()
            self._save_group_membership(user)
        return user

    def _get_default_password(self):
        business_group = self.cleaned_data.get('business_group')
        if business_group:
            profile, _ = GroupProfile.objects.get_or_create(
                group=business_group,
                defaults={'default_password': settings.ADMIN_DEFAULT_PASSWORD},
            )
            if profile.default_password:
                return profile.default_password
        return settings.ADMIN_DEFAULT_PASSWORD

    def _save_group_membership(self, user):
        business_group = self.cleaned_data.get('business_group')
        if business_group:
            UserGroupMembership.objects.update_or_create(
                user=user,
                defaults={'group': business_group},
            )
        else:
            UserGroupMembership.objects.filter(user=user).delete()


class ManagedGroupForm(forms.ModelForm):
    default_password = forms.CharField(
        label='新账号默认密码',
        required=False,
        initial=settings.ADMIN_DEFAULT_PASSWORD,
        help_text='分组下新账号留空密码时，将使用这里的默认密码。',
    )
    default_cover = forms.FileField(
        label='音频默认图片',
        required=False,
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp']),
            validate_group_cover_size,
        ],
        help_text='支持 JPG、PNG、WEBP，大小不超过 100KB。',
    )
    is_default_group = forms.BooleanField(
        label='默认分组',
        required=False,
        help_text='默认分组中的音频对所有账号可见。',
    )
    weight = forms.IntegerField(
        label='权重',
        required=False,
        min_value=1,
        initial=100,
        help_text='数字越低，首页分组排序越靠前。',
    )

    class Meta:
        model = ManagedGroup
        fields = ('name', 'default_password', 'default_cover', 'is_default_group', 'weight')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            profile, _ = GroupProfile.objects.get_or_create(
                group=self.instance,
                defaults={'default_password': settings.ADMIN_DEFAULT_PASSWORD},
            )
            self.fields['default_password'].initial = profile.default_password
            self.fields['default_cover'].initial = profile.default_cover
            self.fields['is_default_group'].initial = profile.is_default_group
            self.fields['weight'].initial = profile.weight

    def save(self, commit=True):
        group = super().save(commit=commit)
        default_password = self.cleaned_data.get('default_password') or settings.ADMIN_DEFAULT_PASSWORD
        default_cover = self.cleaned_data.get('default_cover')
        is_default_group = self.cleaned_data.get('is_default_group', False)
        weight = self.cleaned_data.get('weight') or 100
        if commit:
            profile, _ = GroupProfile.objects.get_or_create(
                group=group,
                defaults={'default_password': settings.ADMIN_DEFAULT_PASSWORD},
            )
            profile.default_password = default_password
            profile.is_default_group = is_default_group
            profile.weight = weight
            update_fields = ['default_password', 'is_default_group', 'weight', 'updated_at']
            if default_cover:
                profile.default_cover = default_cover
                update_fields.append('default_cover')
            profile.save(update_fields=update_fields)
        else:
            group._default_password_from_form = default_password
            group._default_cover_from_form = default_cover
            group._is_default_group_from_form = is_default_group
            group._weight_from_form = weight
        return group
