from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from apps.accounts.models import CustomUser


from django.contrib.auth import authenticate

class CustomAuthenticationForm(AuthenticationForm):
    """
    Subclass of Django's default authentication form that checks for is_active status
    and raises a custom, user-friendly validation error if the user account is inactive.
    """
    def clean(self):
        username = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")

        if username and password:
            self.user_cache = authenticate(
                self.request, username=username, password=password
            )
            if self.user_cache is None:
                # Check if the user exists, password matches, but user is inactive
                try:
                    user = CustomUser.objects.get(username=username)
                    if user.check_password(password) and not user.is_active:
                        self.confirm_login_allowed(user)
                except CustomUser.DoesNotExist:
                    pass
                
                raise self.get_invalid_login_error()
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data

    def confirm_login_allowed(self, user):
        if not user.is_active:
            raise ValidationError(
                "Tu cuenta está en proceso de revisión por un administrador. "
                "Te notificaremos cuando sea habilitada para ingresar.",
                code='inactive',
            )


class StudentSignUpForm(forms.ModelForm):
    """
    Form for registering a new student.
    Forces is_active = False by default.
    """
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl bg-slate-900 border border-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-white placeholder-slate-500 text-sm',
            'x-bind:type': "showPassword ? 'text' : 'password'"
        })
    )
    confirm_password = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl bg-slate-900 border border-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-white placeholder-slate-500 text-sm',
            'x-bind:type': "showConfirmPassword ? 'text' : 'password'"
        })
    )

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 'phone')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-xl bg-slate-900 border border-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-white placeholder-slate-500 text-sm'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-3 rounded-xl bg-slate-900 border border-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-white placeholder-slate-500 text-sm'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-xl bg-slate-900 border border-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-white placeholder-slate-500 text-sm'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-xl bg-slate-900 border border-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-white placeholder-slate-500 text-sm'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-xl bg-slate-900 border border-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-white placeholder-slate-500 text-sm'
            }),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError("Ya existe una cuenta con esta dirección de correo electrónico.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            raise ValidationError("Las contraseñas no coinciden. Por favor introdúcelas de nuevo.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        user.role = CustomUser.Role.STUDENT
        user.is_active = False  # Set to inactive by default for admin approval!
        if commit:
            user.save()
        return user


class UserProfileForm(forms.ModelForm):
    """
    Form for a user to edit their profile details.
    """
    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'phone', 'bio')
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-xl bg-slate-900 border border-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-white placeholder-slate-500 text-sm'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-xl bg-slate-900 border border-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-white placeholder-slate-500 text-sm'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-xl bg-slate-900 border border-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-white placeholder-slate-500 text-sm'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 rounded-xl bg-slate-900 border border-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-white placeholder-slate-500 text-sm',
                'rows': 4
            }),
        }
