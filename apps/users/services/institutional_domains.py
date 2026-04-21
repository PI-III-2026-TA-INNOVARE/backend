import json
from functools import lru_cache
from pathlib import Path
from django.conf import settings

class InstitutionalDomainsUnavailable(Exception):
    pass

def normalize_domain(domain):
    return domain.strip().lower().rstrip('.')

@lru_cache(maxsize=1)
def load_institutional_domains():
    path = Path(settings.INSTITUTIONAL_DOMAINS_FILE)

    if not path.exists():
        raise InstitutionalDomainsUnavailable(
            f'Arquivo de dominios institucionais nao encontrado em {path}.'
        )

    try:
        payload = json.loads(path.read_text(encoding='utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InstitutionalDomainsUnavailable(
            'Arquivo de dominios institucionais invalido.'
        ) from exc

    if not isinstance(payload, list):
        raise InstitutionalDomainsUnavailable(
            'Estrutura invalida: esperado uma lista de universidades.'
        )

    domains = set()
    for university in payload:
        if not isinstance(university, dict):
            continue

        domain_list = university.get('domains')
        if isinstance(domain_list, list):
            for domain in domain_list:
                if isinstance(domain, str):
                    normalized = normalize_domain(domain)
                    if normalized:
                        domains.add(normalized)

        single_domain = university.get('domain')
        if isinstance(single_domain, str):
            normalized = normalize_domain(single_domain)
            if normalized:
                domains.add(normalized)

    if not domains:
        raise InstitutionalDomainsUnavailable(
            'Nenhum dominio institucional foi encontrado no arquivo configurado.'
        )
    
    return domains

def is_institutional_email_domain(email_domain):
    normalized_email_domain = normalize_domain(email_domain)
    if not normalized_email_domain:
        return False

    known_domains = load_institutional_domains()
    if normalized_email_domain in known_domains:
        return True

    for institutional_domain in known_domains:
        if normalized_email_domain.endswith(f'.{institutional_domain}'):
            return True

    return False