"""
Autenticação simples do painel/API — RNF02.

RNF02 exige que dados de transações (sensíveis) só sejam acessíveis a
usuários autenticados. Para o escopo deste TCC, implementamos
autenticação por API Key (um token fixo, enviado no header
"X-API-Key") — mais simples que OAuth/JWT completo, mas já cumpre o
requisito de exigir autenticação para acessar os dados.

Em uma evolução futura (fora do escopo do MVP), isso poderia virar
autenticação de usuário real com login/senha e perfis de acesso.
"""

from functools import wraps

from flask import current_app, jsonify, request


def requer_autenticacao(f):
    """
    Decorator que exige o header "X-API-Key" com o valor configurado
    em Config.API_KEY. Usado nas rotas que expõem dados de transações
    (sensíveis, conforme RNF02).
    """

    @wraps(f)
    def decorada(*args, **kwargs):
        chave_enviada = request.headers.get("X-API-Key")
        chave_esperada = current_app.config.get("API_KEY")

        if not chave_esperada:
            # Se a app não tiver uma API_KEY configurada, algo está
            # errado na configuração — falha de forma segura (nega
            # acesso) em vez de deixar passar sem autenticação.
            return jsonify({
                "erro": "Autenticação não configurada no servidor."
            }), 500

        if not chave_enviada or chave_enviada != chave_esperada:
            return jsonify({
                "erro": "Não autenticado. Envie o header 'X-API-Key' com uma chave válida."
            }), 401

        return f(*args, **kwargs)

    return decorada
