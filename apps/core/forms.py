from django import forms
from .models import (
    Torneio, RegraPontuacao, Equipe, Jogador,
    Fase, Grupo, Partida, SetResult
)


class TailwindInput(forms.TextInput):
    def __init__(self, **kwargs):
        attrs = kwargs.pop('attrs', {})
        attrs.setdefault('class', 'w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition')
        super().__init__(attrs=attrs, **kwargs)


class TailwindSelect(forms.Select):
    def __init__(self, **kwargs):
        attrs = kwargs.pop('attrs', {})
        attrs.setdefault('class', 'w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition bg-white')
        super().__init__(attrs=attrs, **kwargs)


class TailwindNumberInput(forms.NumberInput):
    def __init__(self, **kwargs):
        attrs = kwargs.pop('attrs', {})
        attrs.setdefault('class', 'w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition')
        super().__init__(attrs=attrs, **kwargs)


class TailwindDateInput(forms.DateInput):
    def __init__(self, **kwargs):
        attrs = kwargs.pop('attrs', {})
        attrs.setdefault('class', 'w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition')
        attrs.setdefault('type', 'date')
        super().__init__(attrs=attrs, format='%Y-%m-%d', **kwargs)


class TailwindTimeInput(forms.TimeInput):
    def __init__(self, **kwargs):
        attrs = kwargs.pop('attrs', {})
        attrs.setdefault('class', 'w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition')
        attrs.setdefault('type', 'time')
        super().__init__(attrs=attrs, **kwargs)


class TailwindCheckbox(forms.CheckboxInput):
    def __init__(self, **kwargs):
        attrs = kwargs.pop('attrs', {})
        attrs.setdefault('class', 'h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500')
        super().__init__(attrs=attrs, **kwargs)


class TorneioForm(forms.ModelForm):
    class Meta:
        model = Torneio
        fields = ['nome', 'modalidade', 'local', 'data_inicio', 'hora_inicio', 'jogadores_por_equipe', 'status']
        widgets = {
            'nome': TailwindInput(),
            'modalidade': TailwindInput(),
            'local': TailwindInput(),
            'data_inicio': TailwindDateInput(),
            'hora_inicio': TailwindTimeInput(),
            'jogadores_por_equipe': TailwindNumberInput(),
            'status': TailwindSelect(),
        }


class RegraPontuacaoForm(forms.ModelForm):
    class Meta:
        model = RegraPontuacao
        fields = ['nome', 'sets_para_vencer', 'pontos_por_set', 'tem_vantagem', 'limite_pontos_diretos']
        widgets = {
            'nome': TailwindInput(),
            'sets_para_vencer': TailwindNumberInput(),
            'pontos_por_set': TailwindNumberInput(),
            'tem_vantagem': TailwindCheckbox(),
            'limite_pontos_diretos': TailwindNumberInput(),
        }


class EquipeForm(forms.ModelForm):
    class Meta:
        model = Equipe
        fields = ['nome']
        widgets = {
            'nome': TailwindInput(),
        }


class JogadorForm(forms.ModelForm):
    class Meta:
        model = Jogador
        fields = ['nome', 'apelido', 'posicao']
        widgets = {
            'nome': TailwindInput(),
            'apelido': TailwindInput(),
            'posicao': TailwindInput(),
        }


JogadorFormSet = forms.inlineformset_factory(
    Equipe, Jogador,
    form=JogadorForm,
    extra=2,
    can_delete=True,
)


class FaseForm(forms.ModelForm):
    class Meta:
        model = Fase
        fields = ['nome', 'tipo', 'regra', 'ordem', 'equipes_avancam']
        widgets = {
            'nome': TailwindInput(),
            'tipo': TailwindSelect(),
            'regra': TailwindSelect(),
            'ordem': TailwindNumberInput(),
            'equipes_avancam': TailwindNumberInput(),
        }


class GrupoForm(forms.ModelForm):
    class Meta:
        model = Grupo
        fields = ['nome', 'equipes']
        widgets = {
            'nome': TailwindInput(),
            'equipes': forms.CheckboxSelectMultiple(),
        }


class PartidaForm(forms.ModelForm):
    class Meta:
        model = Partida
        fields = ['fase', 'grupo', 'equipe_a', 'equipe_b', 'status', 'vencedor', 'is_wo', 'vencedor_wo', 'ordem_cronograma']
        widgets = {
            'fase': TailwindSelect(),
            'grupo': TailwindSelect(),
            'equipe_a': TailwindSelect(),
            'equipe_b': TailwindSelect(),
            'status': TailwindSelect(),
            'vencedor': TailwindSelect(),
            'is_wo': TailwindCheckbox(),
            'vencedor_wo': TailwindSelect(),
            'ordem_cronograma': TailwindNumberInput(),
        }


class SetResultForm(forms.ModelForm):
    class Meta:
        model = SetResult
        fields = ['numero_set', 'pontos_a', 'pontos_b']
        widgets = {
            'numero_set': TailwindNumberInput(),
            'pontos_a': TailwindNumberInput(),
            'pontos_b': TailwindNumberInput(),
        }


SetResultFormSet = forms.inlineformset_factory(
    Partida, SetResult,
    form=SetResultForm,
    extra=1,
    can_delete=True,
)
