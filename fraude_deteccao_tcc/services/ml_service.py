"""
Serviço de Machine Learning.

Responsável por carregar o modelo treinado (gerado pelo script
ml/train.py — que faremos na próxima etapa) e realizar a inferência
sobre novas transações.

Mantido separado das rotas Flask (routes/) para que a lógica de ML
possa ser testada e reaproveitada de forma independente da camada web —
isso também facilita comparar/trocar o algoritmo ativo (Regressão
Logística, Árvore de Decisão, Random Forest) sem mexer na API.
"""

import time

import joblib
import numpy as np


class MLService:
    def __init__(self, modelo_path: str):
        self.modelo_path = modelo_path
        self.modelo = None
        self.nome_colunas = None
        self.versao_modelo = None
        self._carregar_modelo()

    def _carregar_modelo(self):
        """
        Carrega o modelo serializado (.pkl) do disco.

        O arquivo é esperado no formato salvo por ml/train.py:
        um dicionário com as chaves "modelo", "colunas" e "versao".
        """
        try:
            artefato = joblib.load(self.modelo_path)
            self.modelo = artefato["modelo"]
            self.nome_colunas = artefato["colunas"]
            self.versao_modelo = artefato.get("versao", "desconhecida")
        except FileNotFoundError:
            # Nenhum modelo treinado ainda — normal antes de rodar ml/train.py.
            # A API sobe mesmo assim, mas /transacoes/classificar retorna erro
            # até que um modelo exista.
            self.modelo = None
            self.nome_colunas = None
            self.versao_modelo = None

    def modelo_disponivel(self) -> bool:
        return self.modelo is not None

    def classificar(self, features: dict) -> dict:
        """
        Recebe um dicionário de features de uma transação e retorna:
        {
            "score": float (0 a 1, probabilidade de fraude),
            "classe_prevista": "fraude" | "legitima",
            "tempo_resposta_ms": float,
            "versao_modelo": str
        }

        RNF01: o tempo de resposta deve ser menor que 500ms por
        transação — por isso medimos e retornamos esse tempo, para que
        possa ser monitorado/registrado.
        """
        if not self.modelo_disponivel():
            raise RuntimeError(
                "Nenhum modelo treinado encontrado. Rode ml/train.py primeiro."
            )

        inicio = time.perf_counter()

        # Monta o vetor de entrada na mesma ordem de colunas usada no treino
        vetor = np.array([[features.get(col, 0.0) for col in self.nome_colunas]])

        # predict_proba retorna [prob_classe_0, prob_classe_1]; assumimos
        # que a classe 1 = fraude (convenção usada no dataset Kaggle)
        probabilidade_fraude = float(self.modelo.predict_proba(vetor)[0][1])

        tempo_resposta_ms = (time.perf_counter() - inicio) * 1000

        return {
            "score": round(probabilidade_fraude, 4),
            "classe_prevista": "fraude" if probabilidade_fraude >= 0.5 else "legitima",
            "tempo_resposta_ms": round(tempo_resposta_ms, 2),
            "versao_modelo": self.versao_modelo,
        }


# Instância única do serviço, criada quando a app inicia (ver app.py).
# Fica None até ser inicializada por init_ml_service().
ml_service: "MLService | None" = None


def init_ml_service(modelo_path: str):
    global ml_service
    ml_service = MLService(modelo_path)
    return ml_service
