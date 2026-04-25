import json
from urllib import error, parse, request

class InvalidCNPJError(Exception):
    pass

class CNPJNotFoundError(Exception):
    pass

class CNPJProviderError(Exception):
    def __init__(self, message, provider_status=None):
        super().__init__(message)
        self.provider_status = provider_status

def normalize_cnpj(cnpj):
    return ''.join(ch for ch in str(cnpj or '') if ch.isdigit())

def is_valid_cnpj(cnpj):
    digits = normalize_cnpj(cnpj)
    if len(digits) != 14:
        return False
    if digits == digits[0] * 14:
        return False

    numbers = [int(d) for d in digits]

    weights_1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    sum_1 = sum(n * w for n, w in zip(numbers[:12], weights_1))
    check_1 = 11 - (sum_1 % 11)
    check_1 = 0 if check_1 >= 10 else check_1

    weights_2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    sum_2 = sum(n * w for n, w in zip(numbers[:12] + [check_1], weights_2))
    check_2 = 11 - (sum_2 % 11)
    check_2 = 0 if check_2 >= 10 else check_2

    return numbers[12] == check_1 and numbers[13] == check_2

def _to_upper(value):
    if value is None:
        return None
    value = str(value).strip()
    if not value:
        return None
    return value.upper()

def _to_digits(value):
    digits = ''.join(ch for ch in str(value or '') if ch.isdigit())
    return digits or None

def fetch_cnpj_data(cnpj):
    normalized = normalize_cnpj(cnpj)
    if not is_valid_cnpj(normalized):
        raise InvalidCNPJError('CNPJ invalido.')

    endpoint = f'https://api.opencnpj.org/{parse.quote(normalized)}?datasets=receita'
    req = request.Request(
        endpoint,
        headers={
            'User-Agent': 'PDConnect-Backend/1.0',
            'Accept': 'application/json',
        },
    )

    try:
        with request.urlopen(req, timeout=10) as resp:
            raw = resp.read()
    except error.HTTPError as exc:
        if exc.code == 404:
            raise CNPJNotFoundError('CNPJ não encontrado.') from exc
        if exc.code == 429:
            raise CNPJProviderError(
                'Limite de requisições excedido no provedor de CNPJ.',
                provider_status=exc.code,
            ) from exc
        raise CNPJProviderError(
            f'Falha ao consultar provedor de CNPJ (HTTP {exc.code}).',
            provider_status=exc.code,
        ) from exc
    except error.URLError as exc:
        raise CNPJProviderError('Falha de comunicação com provedor de CNPJ.') from exc

    try:
        payload = json.loads(raw.decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CNPJProviderError('Resposta inválida do provedor de CNPJ.') from exc

    source = payload.get('receita') if isinstance(payload.get('receita'), dict) else payload

    registration_status = _to_upper(source.get('situacao_cadastral'))
    legal_name = source.get('razao_social')

    company_data = {
        'cnpj': normalize_cnpj(source.get('cnpj') or normalized),
        'razao_social': legal_name,
        'situacao_cadastral': registration_status,
        'municipio': _to_upper(source.get('municipio')),
        'uf': _to_upper(source.get('uf')),
        'endereco': {
            'logradouro': source.get('logradouro'),
            'numero': source.get('numero'),
            'complemento': source.get('complemento'),
            'bairro': source.get('bairro'),
            'cep': _to_digits(source.get('cep')),
        },
    }

    is_active = registration_status == 'ATIVA'
    company_data['pode_cadastrar'] = is_active
    company_data['motivo_bloqueio'] = None if is_active else 'Situação cadastral diferente de ATIVA.'
    return company_data
