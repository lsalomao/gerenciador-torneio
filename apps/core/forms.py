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
        fields = [
            'nome', 'modalidade', 'local', 'data_inicio', 'hora_inicio',
            'slug', 'polling_interval', 'live_url',
            'jogadores_por_equipe', 'quantidade_times', 'formato_torneio',
            'times_por_grupo', 'status'
        ]
        widgets = {
            'nome': TailwindInput(),
            'modalidade': TailwindInput(),
            'local': TailwindInput(),
            'data_inicio': TailwindDateInput(),
            'hora_inicio': TailwindTimeInput(),
            'slug': TailwindInput(),
            'polling_interval': TailwindNumberInput(),
            'live_url': TailwindInput(),
            'jogadores_por_equipe': TailwindNumberInput(),
            'quantidade_times': TailwindSelect(),
            'formato_torneio': TailwindSelect(),
            'times_por_grupo': TailwindSelect(),
            'status': TailwindSelect(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Tornar times_por_grupo não obrigatório por padrão
        self.fields['times_por_grupo'].required = False
        # Adicionar classes customizadas e data attributes
        self.fields['quantidade_times'].required = True
        self.fields['formato_torneio'].required = True

        # Add data attribute para JavaScript
        self.fields['quantidade_times'].widget.attrs['data-field'] = 'quantidade_times'
        self.fields['formato_torneio'].widget.attrs['data-field'] = 'formato_torneio'
        self.fields['times_por_grupo'].widget.attrs['data-field'] = 'times_por_grupo'

    def clean(self):
        cleaned_data = super().clean()
        formato = cleaned_data.get('formato_torneio')
        times_por_grupo = cleaned_data.get('times_por_grupo')

        # Se formato é grupos_e_eliminatoria, times_por_grupo deve estar preenchido
        if formato == 'grupos_e_eliminatoria' and not times_por_grupo:
            self.add_error('times_por_grupo', 'Este campo é obrigatório para formato "Grupos + Eliminatória".')

        return cleaned_data


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

    def __init__(self, *args, **kwargs):
        self.torneio = kwargs.pop('torneio', None)
        super().__init__(*args, **kwargs)

    def clean_nome(self):
        nome = (self.cleaned_data.get('nome') or '').strip()
        torneio = self.torneio or getattr(self.instance, 'torneio', None)

        if torneio and Equipe.objects.filter(torneio=torneio, nome__iexact=nome).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Já existe uma equipe com este nome neste torneio.')

        return nome


class JogadorForm(forms.ModelForm):
    class Meta:
        model = Jogador
        fields = ['nome', 'apelido', 'posicao', 'celular', 'tamanho_camisa']
        widgets = {
            'nome': TailwindInput(),
            'apelido': TailwindInput(),
            'posicao': TailwindInput(),
            'celular': TailwindInput(),
            'tamanho_camisa': TailwindSelect(),
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
        fields = ['nome', 'tipo', 'regra', 'ordem', 'equipes_avancam', 'is_ativa']
        widgets = {
            'nome': TailwindInput(),
            'tipo': TailwindSelect(),
            'regra': TailwindSelect(),
            'ordem': TailwindNumberInput(),
            'equipes_avancam': TailwindNumberInput(),
            'is_ativa': TailwindCheckbox(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Tornar "equipes_avancam" não obrigatório já que será opcional para ELIMINATORIA
        self.fields['equipes_avancam'].required = False

    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo')
        equipes_avancam = cleaned_data.get('equipes_avancam')

        # Validar: equipes_avancam é obrigatório apenas para GRUPO
        if tipo == 'GRUPO' and not equipes_avancam:
            self.add_error('equipes_avancam', 'Este campo é obrigatório para fases do tipo GRUPO.')

        return cleaned_data


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
