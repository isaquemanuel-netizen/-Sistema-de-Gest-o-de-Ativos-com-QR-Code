#!/usr/bin/env python3
"""
Script de migração do banco de dados
Adiciona novas tabelas para: histórico, fotos, categorias e manutenções
"""

import sqlite3
import os
from datetime import datetime

DB = "ativos.db"

def migrate_database():
    """Executa todas as migrações necessárias"""

    print("=" * 60)
    print("  MIGRAÇÃO DO BANCO DE DADOS")
    print("=" * 60)
    print()

    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()

        # 1. CATEGORIAS
        print("1. Criando tabela de CATEGORIAS...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categorias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL UNIQUE,
                descricao TEXT,
                icone TEXT,
                cor TEXT,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Inserir categorias padrão
        categorias_padrao = [
            ('Hardware', 'Equipamentos de informática', 'bi-laptop', '#3498db'),
            ('Móveis', 'Mobiliário de escritório', 'bi-door-open', '#95a5a6'),
            ('Periféricos', 'Periféricos de computador', 'bi-keyboard', '#9b59b6'),
            ('Impressoras', 'Impressoras e scanners', 'bi-printer', '#e74c3c'),
            ('Telefonia', 'Equipamentos de telefonia', 'bi-telephone', '#2ecc71'),
            ('Rede', 'Equipamentos de rede', 'bi-router', '#f39c12'),
            ('Áudio/Vídeo', 'Equipamentos de áudio e vídeo', 'bi-camera-video', '#e67e22'),
            ('Outros', 'Outros ativos', 'bi-box', '#34495e')
        ]

        for cat in categorias_padrao:
            try:
                cursor.execute('''
                    INSERT INTO categorias (nome, descricao, icone, cor)
                    VALUES (?, ?, ?, ?)
                ''', cat)
            except sqlite3.IntegrityError:
                pass  # Categoria já existe

        print("   ✓ Categorias criadas")

        # 2. HISTÓRICO/AUDITORIA
        print("2. Criando tabela de HISTÓRICO...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS historico (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ativo_id INTEGER NOT NULL,
                acao TEXT NOT NULL,
                campo TEXT,
                valor_anterior TEXT,
                valor_novo TEXT,
                usuario TEXT DEFAULT 'Sistema',
                ip_address TEXT,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ativo_id) REFERENCES ativos (id) ON DELETE CASCADE
            )
        ''')
        print("   ✓ Histórico criado")

        # 3. FOTOS/ANEXOS
        print("3. Criando tabela de FOTOS/ANEXOS...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS anexos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ativo_id INTEGER NOT NULL,
                tipo TEXT NOT NULL,
                nome_arquivo TEXT NOT NULL,
                caminho TEXT NOT NULL,
                tamanho INTEGER,
                mime_type TEXT,
                descricao TEXT,
                principal BOOLEAN DEFAULT 0,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ativo_id) REFERENCES ativos (id) ON DELETE CASCADE
            )
        ''')
        print("   ✓ Anexos criados")

        # 4. MANUTENÇÕES
        print("4. Criando tabela de MANUTENÇÕES...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS manutencoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ativo_id INTEGER NOT NULL,
                tipo TEXT NOT NULL,
                descricao TEXT NOT NULL,
                data_manutencao DATE NOT NULL,
                proximo_agendamento DATE,
                responsavel TEXT,
                custo REAL,
                status TEXT DEFAULT 'Concluída',
                observacoes TEXT,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ativo_id) REFERENCES ativos (id) ON DELETE CASCADE
            )
        ''')
        print("   ✓ Manutenções criadas")

        # 5. ADICIONAR COLUNA CATEGORIA_ID NA TABELA ATIVOS
        print("5. Adicionando coluna CATEGORIA_ID aos ativos...")
        try:
            cursor.execute('ALTER TABLE ativos ADD COLUMN categoria_id INTEGER')
            cursor.execute('ALTER TABLE ativos ADD COLUMN subcategoria TEXT')
            print("   ✓ Colunas adicionadas")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("   ⚠ Colunas já existem")
            else:
                raise

        # 6. ADICIONAR CAMPOS EXTRAS AOS ATIVOS
        print("6. Adicionando campos extras aos ativos...")
        campos_extras = [
            ('numero_patrimonio', 'TEXT'),
            ('data_aquisicao', 'DATE'),
            ('valor_aquisicao', 'REAL'),
            ('fornecedor', 'TEXT'),
            ('garantia_ate', 'DATE'),
            ('observacoes', 'TEXT')
        ]

        for campo, tipo in campos_extras:
            try:
                cursor.execute(f'ALTER TABLE ativos ADD COLUMN {campo} {tipo}')
                print(f"   ✓ Campo {campo} adicionado")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    print(f"   ⚠ Campo {campo} já existe")
                else:
                    raise

        # 7. CRIAR ÍNDICES PARA PERFORMANCE
        print("7. Criando índices...")
        indices = [
            'CREATE INDEX IF NOT EXISTS idx_historico_ativo ON historico(ativo_id)',
            'CREATE INDEX IF NOT EXISTS idx_historico_data ON historico(criado_em)',
            'CREATE INDEX IF NOT EXISTS idx_anexos_ativo ON anexos(ativo_id)',
            'CREATE INDEX IF NOT EXISTS idx_manutencoes_ativo ON manutencoes(ativo_id)',
            'CREATE INDEX IF NOT EXISTS idx_manutencoes_data ON manutencoes(data_manutencao)',
            'CREATE INDEX IF NOT EXISTS idx_ativos_categoria ON ativos(categoria_id)'
        ]

        for idx in indices:
            cursor.execute(idx)

        print("   ✓ Índices criados")

        conn.commit()

    print()
    print("=" * 60)
    print("  ✓ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
    print("=" * 60)
    print()
    print("Novas funcionalidades disponíveis:")
    print("  • Histórico de alterações")
    print("  • Upload de fotos e anexos")
    print("  • Categorias e tipos de ativos")
    print("  • Sistema de manutenção")
    print()

if __name__ == '__main__':
    if not os.path.exists(DB):
        print(f"❌ Banco de dados '{DB}' não encontrado!")
        print("   Execute o sistema primeiro para criar o banco.")
        exit(1)

    try:
        migrate_database()
    except Exception as e:
        print(f"\n❌ Erro durante a migração: {str(e)}")
        exit(1)
