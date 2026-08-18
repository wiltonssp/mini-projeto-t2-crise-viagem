"""
Arquitetura multi-tenant para operação B2B.

v3.0: Permite que múltiplas companhias aéreas operem na mesma plataforma
com isolamento de dados, configurações personalizadas e branding independente.
"""

import json
import logging
import os
import sqlite3
import threading
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

_DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
_DB_PATH = os.path.join(_DB_DIR, "tenants.db")


class ConfiguracaoTenant:
    """Configuração personalizada de um tenant (companhia aérea)."""

    def __init__(self, dados: dict):
        self.tenant_id: str = dados.get("tenant_id", "default")
        self.nome: str = dados.get("nome", "Viagem Inteligente")
        self.nome_exibicao: str = dados.get("nome_exibicao", "Viagem Inteligente")
        self.logo_url: str = dados.get("logo_url", "")
        self.cor_primaria: str = dados.get("cor_primaria", "#1a73e8")
        self.cor_secundaria: str = dados.get("cor_secundaria", "#ffffff")
        self.idioma_padrao: str = dados.get("idioma_padrao", "pt")
        self.modelo_llm: str = dados.get("modelo_llm", "openai/gpt-oss-120b")
        self.temperatura_llm: float = dados.get("temperatura_llm", 0.3)
        self.max_sessoes_simultaneas: int = dados.get("max_sessoes_simultaneas", 100)
        self.ativo: bool = dados.get("ativo", True)
        self.plano: str = dados.get("plano", "basico")  # basico, profissional, enterprise
        self.funcionalidades: list[str] = dados.get("funcionalidades", [
            "chat_web", "consulta_voo", "consulta_clima",
            "rag_basico", "plano_contingencia"
        ])
        self.apis_configuradas: dict = dados.get("apis_configuradas", {})
        self.documentos_customizados: list[dict] = dados.get("documentos_customizados", [])
        self.prompt_sistema_custom: str = dados.get("prompt_sistema_custom", "")
        self.webhook_url: str = dados.get("webhook_url", "")
        self.contato_suporte: str = dados.get("contato_suporte", "")
        self.criado_em: str = dados.get("criado_em", "")
        self.atualizado_em: str = dados.get("atualizado_em", "")

    def tem_funcionalidade(self, funcionalidade: str) -> bool:
        """Verifica se o tenant tem acesso a uma funcionalidade."""
        return funcionalidade in self.funcionalidades

    def to_dict(self) -> dict:
        """Converte para dicionário."""
        return {
            "tenant_id": self.tenant_id,
            "nome": self.nome,
            "nome_exibicao": self.nome_exibicao,
            "logo_url": self.logo_url,
            "cor_primaria": self.cor_primaria,
            "cor_secundaria": self.cor_secundaria,
            "idioma_padrao": self.idioma_padrao,
            "modelo_llm": self.modelo_llm,
            "temperatura_llm": self.temperatura_llm,
            "max_sessoes_simultaneas": self.max_sessoes_simultaneas,
            "ativo": self.ativo,
            "plano": self.plano,
            "funcionalidades": self.funcionalidades,
            "apis_configuradas": self.apis_configuradas,
            "documentos_customizados": self.documentos_customizados,
            "prompt_sistema_custom": self.prompt_sistema_custom,
            "webhook_url": self.webhook_url,
            "contato_suporte": self.contato_suporte,
            "criado_em": self.criado_em,
            "atualizado_em": self.atualizado_em,
        }


# Planos disponíveis com funcionalidades associadas
PLANOS = {
    "basico": {
        "nome": "Básico",
        "funcionalidades": [
            "chat_web", "consulta_voo", "consulta_clima",
            "rag_basico", "plano_contingencia",
        ],
        "max_sessoes": 50,
        "max_documentos_custom": 5,
    },
    "profissional": {
        "nome": "Profissional",
        "funcionalidades": [
            "chat_web", "consulta_voo", "consulta_clima",
            "rag_basico", "rag_embeddings", "plano_contingencia",
            "notificacoes", "messaging", "analytics_basico",
            "multilingual",
        ],
        "max_sessoes": 500,
        "max_documentos_custom": 50,
    },
    "enterprise": {
        "nome": "Enterprise",
        "funcionalidades": [
            "chat_web", "consulta_voo", "consulta_clima",
            "rag_basico", "rag_embeddings", "plano_contingencia",
            "notificacoes", "messaging", "analytics_completo",
            "multilingual", "api_real_aviacao", "pnr_integracao",
            "whitelabel", "sla_prioritario", "webhook_customizado",
            "prompt_customizado", "feedback_loop",
        ],
        "max_sessoes": -1,  # ilimitado
        "max_documentos_custom": -1,
    },
}


class GerenciadorTenants:
    """Gerencia tenants (companhias aéreas) no sistema multi-tenant.

    Responsável por:
    - CRUD de tenants
    - Isolamento de configurações
    - Validação de planos e funcionalidades
    - Gerenciamento de limites
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or _DB_PATH
        self._lock = threading.Lock()
        self._cache: dict[str, ConfiguracaoTenant] = {}
        self._inicializar_db()
        self._criar_tenant_padrao()

    def _inicializar_db(self):
        """Cria tabelas de tenants."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                conn.executescript("""
                    CREATE TABLE IF NOT EXISTS tenants (
                        tenant_id TEXT PRIMARY KEY,
                        nome TEXT NOT NULL,
                        nome_exibicao TEXT NOT NULL,
                        logo_url TEXT DEFAULT '',
                        cor_primaria TEXT DEFAULT '#1a73e8',
                        cor_secundaria TEXT DEFAULT '#ffffff',
                        idioma_padrao TEXT DEFAULT 'pt',
                        modelo_llm TEXT DEFAULT 'openai/gpt-oss-120b',
                        temperatura_llm REAL DEFAULT 0.3,
                        max_sessoes_simultaneas INTEGER DEFAULT 100,
                        ativo INTEGER DEFAULT 1,
                        plano TEXT DEFAULT 'basico',
                        funcionalidades TEXT DEFAULT '[]',
                        apis_configuradas TEXT DEFAULT '{}',
                        documentos_customizados TEXT DEFAULT '[]',
                        prompt_sistema_custom TEXT DEFAULT '',
                        webhook_url TEXT DEFAULT '',
                        contato_suporte TEXT DEFAULT '',
                        criado_em TEXT NOT NULL,
                        atualizado_em TEXT NOT NULL
                    );

                    CREATE TABLE IF NOT EXISTS tenant_uso (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        tenant_id TEXT NOT NULL,
                        mes_referencia TEXT NOT NULL,
                        total_sessoes INTEGER DEFAULT 0,
                        total_mensagens INTEGER DEFAULT 0,
                        total_tokens_llm INTEGER DEFAULT 0,
                        custo_estimado REAL DEFAULT 0.0,
                        FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id),
                        UNIQUE(tenant_id, mes_referencia)
                    );
                """)
                conn.commit()
            finally:
                conn.close()

    def _criar_tenant_padrao(self):
        """Cria o tenant padrão se não existir."""
        if not self.obter_tenant("default"):
            self.criar_tenant(
                tenant_id="default",
                nome="Viagem Inteligente",
                nome_exibicao="Viagem Inteligente — Gestão de Crises",
                plano="enterprise",
            )

    def criar_tenant(self, tenant_id: str, nome: str,
                     nome_exibicao: str = "",
                     plano: str = "basico",
                     **kwargs) -> tuple[bool, str]:
        """Cria um novo tenant.

        Args:
            tenant_id: Identificador único (slug).
            nome: Nome da companhia.
            nome_exibicao: Nome para exibição na interface.
            plano: Plano de serviço (basico, profissional, enterprise).
            **kwargs: Configurações adicionais.

        Returns:
            Tupla (sucesso, mensagem).
        """
        if plano not in PLANOS:
            return False, f"Plano '{plano}' não existe. Opções: {list(PLANOS.keys())}"

        agora = datetime.now().isoformat()
        config_plano = PLANOS[plano]

        funcionalidades = kwargs.get("funcionalidades", config_plano["funcionalidades"])
        max_sessoes = kwargs.get("max_sessoes_simultaneas", config_plano["max_sessoes"])

        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                # Verificar se já existe
                cursor = conn.execute(
                    "SELECT tenant_id FROM tenants WHERE tenant_id = ?", (tenant_id,)
                )
                if cursor.fetchone():
                    return False, f"Tenant '{tenant_id}' já existe."

                conn.execute(
                    """INSERT INTO tenants
                    (tenant_id, nome, nome_exibicao, plano, funcionalidades,
                     max_sessoes_simultaneas, criado_em, atualizado_em,
                     idioma_padrao, modelo_llm, temperatura_llm,
                     logo_url, cor_primaria, cor_secundaria,
                     prompt_sistema_custom, webhook_url, contato_suporte)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        tenant_id, nome, nome_exibicao or nome, plano,
                        json.dumps(funcionalidades), max_sessoes,
                        agora, agora,
                        kwargs.get("idioma_padrao", "pt"),
                        kwargs.get("modelo_llm", "openai/gpt-oss-120b"),
                        kwargs.get("temperatura_llm", 0.3),
                        kwargs.get("logo_url", ""),
                        kwargs.get("cor_primaria", "#1a73e8"),
                        kwargs.get("cor_secundaria", "#ffffff"),
                        kwargs.get("prompt_sistema_custom", ""),
                        kwargs.get("webhook_url", ""),
                        kwargs.get("contato_suporte", ""),
                    )
                )
                conn.commit()

                # Invalidar cache
                self._cache.pop(tenant_id, None)
                return True, f"Tenant '{tenant_id}' criado com plano '{plano}'."
            finally:
                conn.close()

    def obter_tenant(self, tenant_id: str) -> Optional[ConfiguracaoTenant]:
        """Obtém configuração de um tenant.

        Args:
            tenant_id: ID do tenant.

        Returns:
            ConfiguracaoTenant ou None se não encontrado.
        """
        # Verificar cache
        if tenant_id in self._cache:
            return self._cache[tenant_id]

        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                cursor = conn.execute(
                    "SELECT * FROM tenants WHERE tenant_id = ?", (tenant_id,)
                )
                row = cursor.fetchone()
                if not row:
                    return None

                # Mapear colunas para dict
                colunas = [desc[0] for desc in cursor.description]
                dados = dict(zip(colunas, row))

                # Deserializar JSON
                dados["funcionalidades"] = json.loads(dados.get("funcionalidades", "[]"))
                dados["apis_configuradas"] = json.loads(dados.get("apis_configuradas", "{}"))
                dados["documentos_customizados"] = json.loads(
                    dados.get("documentos_customizados", "[]")
                )
                dados["ativo"] = bool(dados.get("ativo", 1))

                config = ConfiguracaoTenant(dados)
                self._cache[tenant_id] = config
                return config
            finally:
                conn.close()

    def atualizar_tenant(self, tenant_id: str, **kwargs) -> bool:
        """Atualiza configurações de um tenant.

        Args:
            tenant_id: ID do tenant.
            **kwargs: Campos a atualizar.

        Returns:
            True se atualizou com sucesso.
        """
        campos_validos = {
            "nome", "nome_exibicao", "logo_url", "cor_primaria", "cor_secundaria",
            "idioma_padrao", "modelo_llm", "temperatura_llm",
            "max_sessoes_simultaneas", "ativo", "plano",
            "prompt_sistema_custom", "webhook_url", "contato_suporte",
        }

        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                agora = datetime.now().isoformat()
                for campo, valor in kwargs.items():
                    if campo in campos_validos:
                        conn.execute(
                            f"UPDATE tenants SET {campo} = ?, atualizado_em = ? WHERE tenant_id = ?",
                            (valor, agora, tenant_id)
                        )

                # Campos JSON especiais
                if "funcionalidades" in kwargs:
                    conn.execute(
                        "UPDATE tenants SET funcionalidades = ?, atualizado_em = ? WHERE tenant_id = ?",
                        (json.dumps(kwargs["funcionalidades"]), agora, tenant_id)
                    )
                if "apis_configuradas" in kwargs:
                    conn.execute(
                        "UPDATE tenants SET apis_configuradas = ?, atualizado_em = ? WHERE tenant_id = ?",
                        (json.dumps(kwargs["apis_configuradas"]), agora, tenant_id)
                    )
                if "documentos_customizados" in kwargs:
                    conn.execute(
                        "UPDATE tenants SET documentos_customizados = ?, atualizado_em = ? WHERE tenant_id = ?",
                        (json.dumps(kwargs["documentos_customizados"]), agora, tenant_id)
                    )

                conn.commit()
                # Invalidar cache
                self._cache.pop(tenant_id, None)
                return True
            except Exception as e:
                logger.error("Erro ao atualizar tenant %s: %s", tenant_id, e)
                return False
            finally:
                conn.close()

    def listar_tenants(self, apenas_ativos: bool = True) -> list[dict]:
        """Lista todos os tenants.

        Args:
            apenas_ativos: Se True, retorna apenas tenants ativos.

        Returns:
            Lista de dicts com informações resumidas dos tenants.
        """
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                query = "SELECT tenant_id, nome, nome_exibicao, plano, ativo, criado_em FROM tenants"
                if apenas_ativos:
                    query += " WHERE ativo = 1"
                query += " ORDER BY nome"

                cursor = conn.execute(query)
                return [
                    {
                        "tenant_id": row[0],
                        "nome": row[1],
                        "nome_exibicao": row[2],
                        "plano": row[3],
                        "ativo": bool(row[4]),
                        "criado_em": row[5],
                    }
                    for row in cursor.fetchall()
                ]
            finally:
                conn.close()

    def registrar_uso(self, tenant_id: str, mensagens: int = 1,
                      tokens_llm: int = 0):
        """Registra uso do tenant para controle e cobrança.

        Args:
            tenant_id: ID do tenant.
            mensagens: Número de mensagens processadas.
            tokens_llm: Tokens LLM consumidos.
        """
        mes_ref = datetime.now().strftime("%Y-%m")
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                conn.execute(
                    """INSERT INTO tenant_uso (tenant_id, mes_referencia,
                    total_sessoes, total_mensagens, total_tokens_llm)
                    VALUES (?, ?, 0, ?, ?)
                    ON CONFLICT(tenant_id, mes_referencia) DO UPDATE SET
                    total_mensagens = total_mensagens + ?,
                    total_tokens_llm = total_tokens_llm + ?""",
                    (tenant_id, mes_ref, mensagens, tokens_llm,
                     mensagens, tokens_llm)
                )
                conn.commit()
            except Exception as e:
                logger.error("Erro ao registrar uso do tenant %s: %s", tenant_id, e)
            finally:
                conn.close()

    def obter_uso(self, tenant_id: str, mes: Optional[str] = None) -> dict:
        """Obtém relatório de uso do tenant.

        Args:
            tenant_id: ID do tenant.
            mes: Mês no formato YYYY-MM (default: mês atual).

        Returns:
            Dict com métricas de uso.
        """
        mes_ref = mes or datetime.now().strftime("%Y-%m")
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                cursor = conn.execute(
                    """SELECT total_sessoes, total_mensagens, total_tokens_llm, custo_estimado
                    FROM tenant_uso
                    WHERE tenant_id = ? AND mes_referencia = ?""",
                    (tenant_id, mes_ref)
                )
                row = cursor.fetchone()
                if row:
                    return {
                        "tenant_id": tenant_id,
                        "mes": mes_ref,
                        "total_sessoes": row[0],
                        "total_mensagens": row[1],
                        "total_tokens_llm": row[2],
                        "custo_estimado": row[3],
                    }
                return {
                    "tenant_id": tenant_id,
                    "mes": mes_ref,
                    "total_sessoes": 0,
                    "total_mensagens": 0,
                    "total_tokens_llm": 0,
                    "custo_estimado": 0.0,
                }
            finally:
                conn.close()


# Instância singleton
_gerenciador_tenants: Optional[GerenciadorTenants] = None


def get_gerenciador_tenants(db_path: Optional[str] = None) -> GerenciadorTenants:
    """Retorna instância singleton do gerenciador de tenants."""
    global _gerenciador_tenants
    if _gerenciador_tenants is None:
        _gerenciador_tenants = GerenciadorTenants(db_path)
    return _gerenciador_tenants
