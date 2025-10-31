#!/usr/bin/env python3
"""
Script para criar tabela de usuários e usuário admin inicial
"""
import sqlite3
from werkzeug.security import generate_password_hash

DB = "ativos.db"

def criar_tabela_usuarios():
    with sqlite3.connect(DB) as conn:
        # Criar tabela de usuários
        conn.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                senha_hash TEXT NOT NULL,
                nome TEXT NOT NULL,
                perfil TEXT NOT NULL DEFAULT 'visualizador',
                ativo BOOLEAN DEFAULT 1,
                ultimo_acesso TIMESTAMP,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Verificar se já existe usuário admin
        admin_exists = conn.execute('SELECT COUNT(*) FROM usuarios WHERE username = "admin"').fetchone()[0]

        if admin_exists == 0:
            # Criar usuário admin padrão
            senha_hash = generate_password_hash('admin123')  # ALTERAR EM PRODUÇÃO!
            conn.execute('''
                INSERT INTO usuarios (username, email, senha_hash, nome, perfil, ativo)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', ('admin', 'admin@sistema.com', senha_hash, 'Administrador', 'admin', True))

            print("✅ Usuário admin criado")
            print("   Username: admin")
            print("   Senha: admin123")
            print("   ⚠️  ALTERE A SENHA APÓS O PRIMEIRO LOGIN!")
        else:
            print("ℹ️  Usuário admin já existe")

        conn.commit()
        print("✅ Tabela de usuários criada/atualizada com sucesso")

if __name__ == '__main__':
    criar_tabela_usuarios()
