"""
Módulo de autenticação e gerenciamento de perfil de usuário.

v2.0: Implementa sistema de autenticação simples com SQLite,
suportando perfis de usuário com preferências e histórico.
"""

import hashlib
import logging
import os
import secrets
import sqlite3
import threading
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

_DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
_DB_PATH = os.path.join(_DB_DIR, "usuarios.db")


class GerenciadorUsuarios:
    """Gerencia autenticação e perfis de usuários.

    Suporta:
    - Registro e login com senha hasheada (SHA-256 + salt)
    - Tokens de sessão para autenticação stateless
    - Perfis com preferências e dados de viagem
    - Histórico de reservas por usuário
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or _DB_PATH
        self._lock = threading.Lock()
        self._inicializar_db()

    def _inicializar_db(self):
        """Cria tabelas de usuários se não existirem."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                conn.executescript("""
                    CREATE TABLE IF NOT EXISTS usuarios (
                        id TEXT PRIMARY KEY,
                        email TEXT UNIQUE NOT NULL,
                        nome TEXT NOT NULL,
                        senha_hash TEXT NOT NULL,
                        salt TEXT NOT NULL,
                        criado_em TEXT NOT NULL,
                        ultimo_login TEXT,
                        ativo INTEGER DEFAULT 1,
                        tenant_id TEXT DEFAULT 'default',
                        idioma_preferido TEXT DEFAULT 'pt',
                        telefone TEXT DEFAULT '',
                        telegram_id TEXT DEFAULT '',
                        notificacoes_ativas INTEGER DEFAULT 1
                    );

                    CREATE TABLE IF NOT EXISTS tokens (
                        token TEXT PRIMARY KEY,
                        usuario_id TEXT NOT NULL,
                        criado_em TEXT NOT NULL,
                        expira_em TEXT NOT NULL,
                        ativo INTEGER DEFAULT 1,
                        FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
                    );

                    CREATE TABLE IF NOT EXISTS reservas_usuario (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        usuario_id TEXT NOT NULL,
                        codigo_reserva TEXT NOT NULL,
                        descricao TEXT DEFAULT '',
                        adicionada_em TEXT NOT NULL,
                        monitorar INTEGER DEFAULT 1,
                        FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
                    );

                    CREATE TABLE IF NOT EXISTS preferencias (
                        usuario_id TEXT PRIMARY KEY,
                        canal_notificacao TEXT DEFAULT 'web',
                        receber_alertas_clima INTEGER DEFAULT 1,
                        receber_alertas_voo INTEGER DEFAULT 1,
                        idioma TEXT DEFAULT 'pt',
                        aeroporto_preferido TEXT DEFAULT '',
                        dados_json TEXT DEFAULT '{}',
                        FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
                    );

                    CREATE INDEX IF NOT EXISTS idx_tokens_usuario
                        ON tokens(usuario_id);
                    CREATE INDEX IF NOT EXISTS idx_reservas_usuario
                        ON reservas_usuario(usuario_id);
                """)
                conn.commit()
            finally:
                conn.close()

    def _gerar_hash(self, senha: str, salt: str) -> str:
        """Gera hash SHA-256 da senha com salt."""
        return hashlib.sha256(f"{salt}{senha}".encode()).hexdigest()

    def _gerar_salt(self) -> str:
        """Gera salt aleatório."""
        return secrets.token_hex(16)

    def _gerar_token(self) -> str:
        """Gera token de sessão seguro."""
        return secrets.token_urlsafe(32)

    def _gerar_id(self) -> str:
        """Gera ID único para o usuário."""
        return secrets.token_hex(12)

    def registrar(self, email: str, nome: str, senha: str,
                  tenant_id: str = "default",
                  idioma: str = "pt") -> tuple[bool, str]:
        """Registra um novo usuário.

        Args:
            email: Email do usuário (único).
            nome: Nome completo.
            senha: Senha em texto plano (será hasheada).
            tenant_id: ID do tenant.
            idioma: Idioma preferido.

        Returns:
            Tupla (sucesso: bool, mensagem_ou_id: str).
        """
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                # Verificar email duplicado
                cursor = conn.execute(
                    "SELECT id FROM usuarios WHERE email = ?", (email.lower(),)
                )
                if cursor.fetchone():
                    return False, "Email já cadastrado."

                # Criar usuário
                usuario_id = self._gerar_id()
                salt = self._gerar_salt()
                senha_hash = self._gerar_hash(senha, salt)
                agora = datetime.now().isoformat()

                conn.execute(
                    """INSERT INTO usuarios
                    (id, email, nome, senha_hash, salt, criado_em, tenant_id, idioma_preferido)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (usuario_id, email.lower(), nome, senha_hash, salt,
                     agora, tenant_id, idioma)
                )

                # Criar preferências padrão
                conn.execute(
                    """INSERT INTO preferencias (usuario_id, idioma)
                    VALUES (?, ?)""",
                    (usuario_id, idioma)
                )

                conn.commit()
                return True, usuario_id
            finally:
                conn.close()

    def login(self, email: str, senha: str) -> tuple[bool, str]:
        """Autentica usuário e gera token de sessão.

        Args:
            email: Email do usuário.
            senha: Senha em texto plano.

        Returns:
            Tupla (sucesso: bool, token_ou_erro: str).
        """
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                cursor = conn.execute(
                    "SELECT id, senha_hash, salt, ativo FROM usuarios WHERE email = ?",
                    (email.lower(),)
                )
                row = cursor.fetchone()

                if not row:
                    return False, "Email ou senha inválidos."

                usuario_id, senha_hash, salt, ativo = row

                if not ativo:
                    return False, "Conta desativada."

                # Verificar senha
                hash_tentativa = self._gerar_hash(senha, salt)
                if hash_tentativa != senha_hash:
                    return False, "Email ou senha inválidos."

                # Gerar token
                token = self._gerar_token()
                agora = datetime.now()
                expira = agora + timedelta(hours=24)

                conn.execute(
                    """INSERT INTO tokens (token, usuario_id, criado_em, expira_em)
                    VALUES (?, ?, ?, ?)""",
                    (token, usuario_id, agora.isoformat(), expira.isoformat())
                )

                # Atualizar último login
                conn.execute(
                    "UPDATE usuarios SET ultimo_login = ? WHERE id = ?",
                    (agora.isoformat(), usuario_id)
                )

                conn.commit()
                return True, token
            finally:
                conn.close()

    def validar_token(self, token: str) -> Optional[dict]:
        """Valida token de sessão e retorna dados do usuário.

        Args:
            token: Token de sessão a validar.

        Returns:
            Dict com dados do usuário ou None se inválido.
        """
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                cursor = conn.execute(
                    """SELECT t.usuario_id, t.expira_em, u.email, u.nome,
                    u.tenant_id, u.idioma_preferido
                    FROM tokens t JOIN usuarios u ON t.usuario_id = u.id
                    WHERE t.token = ? AND t.ativo = 1""",
                    (token,)
                )
                row = cursor.fetchone()

                if not row:
                    return None

                usuario_id, expira_em, email, nome, tenant_id, idioma = row

                # Verificar expiração
                if datetime.fromisoformat(expira_em) < datetime.now():
                    # Token expirado — desativar
                    conn.execute(
                        "UPDATE tokens SET ativo = 0 WHERE token = ?", (token,)
                    )
                    conn.commit()
                    return None

                return {
                    "usuario_id": usuario_id,
                    "email": email,
                    "nome": nome,
                    "tenant_id": tenant_id,
                    "idioma": idioma,
                }
            finally:
                conn.close()

    def logout(self, token: str) -> bool:
        """Invalida token de sessão."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                conn.execute(
                    "UPDATE tokens SET ativo = 0 WHERE token = ?", (token,)
                )
                conn.commit()
                return True
            finally:
                conn.close()

    def obter_perfil(self, usuario_id: str) -> Optional[dict]:
        """Retorna perfil completo do usuário.

        Args:
            usuario_id: ID do usuário.

        Returns:
            Dict com dados do perfil ou None.
        """
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                cursor = conn.execute(
                    """SELECT u.id, u.email, u.nome, u.criado_em, u.ultimo_login,
                    u.tenant_id, u.idioma_preferido, u.telefone, u.telegram_id,
                    u.notificacoes_ativas,
                    p.canal_notificacao, p.receber_alertas_clima,
                    p.receber_alertas_voo, p.aeroporto_preferido
                    FROM usuarios u
                    LEFT JOIN preferencias p ON u.id = p.usuario_id
                    WHERE u.id = ?""",
                    (usuario_id,)
                )
                row = cursor.fetchone()
                if not row:
                    return None

                return {
                    "id": row[0],
                    "email": row[1],
                    "nome": row[2],
                    "criado_em": row[3],
                    "ultimo_login": row[4],
                    "tenant_id": row[5],
                    "idioma_preferido": row[6],
                    "telefone": row[7],
                    "telegram_id": row[8],
                    "notificacoes_ativas": bool(row[9]),
                    "canal_notificacao": row[10] or "web",
                    "receber_alertas_clima": bool(row[11]),
                    "receber_alertas_voo": bool(row[12]),
                    "aeroporto_preferido": row[13] or "",
                }
            finally:
                conn.close()

    def atualizar_perfil(self, usuario_id: str, **kwargs) -> bool:
        """Atualiza campos do perfil do usuário.

        Args:
            usuario_id: ID do usuário.
            **kwargs: Campos a atualizar (nome, telefone, idioma, etc.)

        Returns:
            True se atualizou com sucesso.
        """
        campos_usuario = {"nome", "telefone", "telegram_id",
                          "idioma_preferido", "notificacoes_ativas"}
        campos_preferencias = {"canal_notificacao", "receber_alertas_clima",
                               "receber_alertas_voo", "aeroporto_preferido"}

        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                for campo, valor in kwargs.items():
                    if campo in campos_usuario:
                        conn.execute(
                            f"UPDATE usuarios SET {campo} = ? WHERE id = ?",
                            (valor, usuario_id)
                        )
                    elif campo in campos_preferencias:
                        conn.execute(
                            f"UPDATE preferencias SET {campo} = ? WHERE usuario_id = ?",
                            (valor, usuario_id)
                        )
                conn.commit()
                return True
            except Exception as e:
                logger.error("Erro ao atualizar perfil: %s", e)
                return False
            finally:
                conn.close()

    def adicionar_reserva(self, usuario_id: str, codigo_reserva: str,
                          descricao: str = "") -> bool:
        """Adiciona uma reserva ao perfil do usuário para monitoramento.

        Args:
            usuario_id: ID do usuário.
            codigo_reserva: Código da reserva (6 chars).
            descricao: Descrição opcional (ex: "Viagem para o Rio").

        Returns:
            True se adicionou com sucesso.
        """
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                agora = datetime.now().isoformat()
                conn.execute(
                    """INSERT INTO reservas_usuario
                    (usuario_id, codigo_reserva, descricao, adicionada_em)
                    VALUES (?, ?, ?, ?)""",
                    (usuario_id, codigo_reserva.upper(), descricao, agora)
                )
                conn.commit()
                return True
            except Exception as e:
                logger.error("Erro ao adicionar reserva: %s", e)
                return False
            finally:
                conn.close()

    def obter_reservas(self, usuario_id: str) -> list[dict]:
        """Lista reservas do usuário.

        Args:
            usuario_id: ID do usuário.

        Returns:
            Lista de reservas com código, descrição e status de monitoramento.
        """
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                cursor = conn.execute(
                    """SELECT codigo_reserva, descricao, adicionada_em, monitorar
                    FROM reservas_usuario WHERE usuario_id = ?
                    ORDER BY adicionada_em DESC""",
                    (usuario_id,)
                )
                return [
                    {
                        "codigo_reserva": row[0],
                        "descricao": row[1],
                        "adicionada_em": row[2],
                        "monitorar": bool(row[3]),
                    }
                    for row in cursor.fetchall()
                ]
            finally:
                conn.close()


# Instância singleton
_gerenciador_usuarios: Optional[GerenciadorUsuarios] = None


def get_gerenciador_usuarios(db_path: Optional[str] = None) -> GerenciadorUsuarios:
    """Retorna instância singleton do gerenciador de usuários."""
    global _gerenciador_usuarios
    if _gerenciador_usuarios is None:
        _gerenciador_usuarios = GerenciadorUsuarios(db_path)
    return _gerenciador_usuarios
