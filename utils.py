"""
Funções utilitárias para o sistema de gestão de ativos
"""

import sqlite3
import os
from datetime import datetime
from werkzeug.utils import secure_filename

DB = "ativos.db"
UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'xls', 'xlsx'}

# Criar pasta de uploads
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'fotos'), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'documentos'), exist_ok=True)


def allowed_file(filename):
    """Verifica se o arquivo tem extensão permitida"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def registrar_historico(ativo_id, acao, campo=None, valor_anterior=None, valor_novo=None, usuario='Sistema', ip_address=None):
    """
    Registra uma ação no histórico de auditoria

    Args:
        ativo_id: ID do ativo
        acao: Tipo de ação (criado, editado, deletado, etc.)
        campo: Campo que foi alterado (opcional)
        valor_anterior: Valor antes da alteração (opcional)
        valor_novo: Novo valor (opcional)
        usuario: Nome do usuário que fez a ação
        ip_address: IP de onde veio a requisição
    """
    try:
        with sqlite3.connect(DB) as conn:
            conn.execute('''
                INSERT INTO historico (ativo_id, acao, campo, valor_anterior, valor_novo, usuario, ip_address)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (ativo_id, acao, campo, valor_anterior, valor_novo, usuario, ip_address))
            conn.commit()
    except Exception as e:
        print(f"Erro ao registrar histórico: {e}")


def get_historico_ativo(ativo_id):
    """Busca todo o histórico de um ativo"""
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        historico = cursor.execute('''
            SELECT id, acao, campo, valor_anterior, valor_novo, usuario, ip_address, criado_em
            FROM historico
            WHERE ativo_id = ?
            ORDER BY criado_em DESC
        ''', (ativo_id,)).fetchall()
    return historico


def get_anexos_ativo(ativo_id):
    """Busca todos os anexos de um ativo"""
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        anexos = cursor.execute('''
            SELECT id, tipo, nome_arquivo, caminho, tamanho, mime_type, descricao, principal, criado_em
            FROM anexos
            WHERE ativo_id = ?
            ORDER BY principal DESC, criado_em DESC
        ''', (ativo_id,)).fetchall()
    return anexos


def get_foto_principal(ativo_id):
    """Busca a foto principal de um ativo"""
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        foto = cursor.execute('''
            SELECT caminho FROM anexos
            WHERE ativo_id = ? AND tipo = 'foto' AND principal = 1
            LIMIT 1
        ''', (ativo_id,)).fetchone()
    return foto[0] if foto else None


def get_manutencoes_ativo(ativo_id):
    """Busca todas as manutenções de um ativo"""
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        manutencoes = cursor.execute('''
            SELECT id, tipo, descricao, data_manutencao, proximo_agendamento,
                   responsavel, custo, status, observacoes, criado_em
            FROM manutencoes
            WHERE ativo_id = ?
            ORDER BY data_manutencao DESC
        ''', (ativo_id,)).fetchall()
    return manutencoes


def get_proximas_manutencoes(dias=30):
    """Busca manutenções agendadas nos próximos X dias"""
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        manutencoes = cursor.execute('''
            SELECT m.id, m.ativo_id, a.codigo_id, a.nome, m.tipo, m.proximo_agendamento
            FROM manutencoes m
            JOIN ativos a ON m.ativo_id = a.id
            WHERE m.proximo_agendamento IS NOT NULL
              AND m.proximo_agendamento <= date('now', '+' || ? || ' days')
              AND m.proximo_agendamento >= date('now')
            ORDER BY m.proximo_agendamento ASC
        ''', (dias,)).fetchall()
    return manutencoes


def get_categorias():
    """Busca todas as categorias"""
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        categorias = cursor.execute('''
            SELECT id, nome, descricao, icone, cor
            FROM categorias
            ORDER BY nome
        ''').fetchall()
    return categorias


def get_categoria(categoria_id):
    """Busca uma categoria específica"""
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        categoria = cursor.execute('''
            SELECT id, nome, descricao, icone, cor
            FROM categorias
            WHERE id = ?
        ''', (categoria_id,)).fetchone()
    return categoria


def get_estatisticas_categorias():
    """Busca estatísticas de ativos por categoria"""
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        stats = cursor.execute('''
            SELECT c.nome, c.cor, c.icone, COUNT(a.id) as total
            FROM categorias c
            LEFT JOIN ativos a ON c.id = a.categoria_id
            GROUP BY c.id
            ORDER BY total DESC
        ''').fetchall()
    return stats


def formatar_moeda(valor):
    """Formata valor para moeda brasileira"""
    if valor is None:
        return "R$ 0,00"
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def formatar_data(data_str):
    """Formata data no padrão brasileiro"""
    if not data_str:
        return "-"
    try:
        data = datetime.strptime(data_str, '%Y-%m-%d')
        return data.strftime('%d/%m/%Y')
    except:
        return data_str


def calcular_dias_restantes(data_str):
    """Calcula quantos dias faltam para uma data"""
    if not data_str:
        return None
    try:
        data = datetime.strptime(data_str, '%Y-%m-%d')
        hoje = datetime.now()
        delta = (data - hoje).days
        return delta
    except:
        return None
