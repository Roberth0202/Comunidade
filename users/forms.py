from django import forms

class SolicitacaoRedefinicaoSenhaForm(forms.Form):
    email = forms.EmailField(
        label='E-mail',
        max_length=254,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Digite seu email.'})
    )