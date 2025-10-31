#!/usr/bin/env python3
"""
Script de Backup Automático do Banco de Dados
Mantém os últimos 7 backups e rotaciona automaticamente
"""
import sqlite3
import shutil
import os
from datetime import datetime
import glob

DB_FILE = "ativos.db"
BACKUP_DIR = "backups"
MAX_BACKUPS = 7

def criar_backup():
    """Cria backup do banco de dados"""
    try:
        # Criar diretório de backup se não existir
        os.makedirs(BACKUP_DIR, exist_ok=True)

        # Nome do arquivo de backup com timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(BACKUP_DIR, f'ativos_backup_{timestamp}.db')

        # Copiar banco de dados
        if os.path.exists(DB_FILE):
            # Usar VACUUM para compactar antes do backup
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute('VACUUM')

            # Copiar arquivo
            shutil.copy2(DB_FILE, backup_file)
            file_size = os.path.getsize(backup_file) / (1024 * 1024)  # MB

            print(f"✅ Backup criado com sucesso!")
            print(f"   📁 Arquivo: {backup_file}")
            print(f"   📊 Tamanho: {file_size:.2f} MB")
            print(f"   🕐 Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

            # Rotacionar backups antigos
            rotacionar_backups()

            return True
        else:
            print(f"❌ Erro: Banco de dados '{DB_FILE}' não encontrado")
            return False

    except Exception as e:
        print(f"❌ Erro ao criar backup: {e}")
        return False

def rotacionar_backups():
    """Remove backups antigos mantendo apenas os últimos MAX_BACKUPS"""
    try:
        # Listar todos os backups
        backups = sorted(glob.glob(os.path.join(BACKUP_DIR, 'ativos_backup_*.db')))

        if len(backups) > MAX_BACKUPS:
            # Remover os mais antigos
            backups_to_remove = backups[:-MAX_BACKUPS]

            for backup_file in backups_to_remove:
                os.remove(backup_file)
                print(f"   🗑️  Removido backup antigo: {os.path.basename(backup_file)}")

            print(f"   ℹ️  Mantidos {MAX_BACKUPS} backups mais recentes")
        else:
            print(f"   ℹ️  Total de backups: {len(backups)}")

    except Exception as e:
        print(f"⚠️  Erro ao rotacionar backups: {e}")

def listar_backups():
    """Lista todos os backups disponíveis"""
    try:
        backups = sorted(glob.glob(os.path.join(BACKUP_DIR, 'ativos_backup_*.db')), reverse=True)

        if not backups:
            print("ℹ️  Nenhum backup encontrado")
            return

        print("\n📋 Backups disponíveis:")
        print("-" * 70)

        for backup_file in backups:
            file_size = os.path.getsize(backup_file) / (1024 * 1024)
            file_time = datetime.fromtimestamp(os.path.getmtime(backup_file))
            print(f"   📁 {os.path.basename(backup_file)}")
            print(f"      Tamanho: {file_size:.2f} MB")
            print(f"      Data: {file_time.strftime('%d/%m/%Y %H:%M:%S')}")
            print()

    except Exception as e:
        print(f"❌ Erro ao listar backups: {e}")

def restaurar_backup(backup_file):
    """Restaura um backup específico"""
    try:
        if not os.path.exists(backup_file):
            print(f"❌ Backup não encontrado: {backup_file}")
            return False

        # Criar backup do banco atual antes de restaurar
        if os.path.exists(DB_FILE):
            backup_atual = f"{DB_FILE}.before_restore"
            shutil.copy2(DB_FILE, backup_atual)
            print(f"   ℹ️  Backup do banco atual salvo em: {backup_atual}")

        # Restaurar backup
        shutil.copy2(backup_file, DB_FILE)
        print(f"✅ Backup restaurado com sucesso!")
        print(f"   📁 De: {backup_file}")
        print(f"   📁 Para: {DB_FILE}")

        return True

    except Exception as e:
        print(f"❌ Erro ao restaurar backup: {e}")
        return False

if __name__ == '__main__':
    import sys

    print("\n" + "="*70)
    print("  SISTEMA DE BACKUP - Gestão de Ativos")
    print("="*70 + "\n")

    if len(sys.argv) > 1:
        if sys.argv[1] == 'list':
            listar_backups()
        elif sys.argv[1] == 'restore' and len(sys.argv) > 2:
            restaurar_backup(sys.argv[2])
        else:
            print("Uso:")
            print("  python backup_database.py           # Criar backup")
            print("  python backup_database.py list      # Listar backups")
            print("  python backup_database.py restore <arquivo>  # Restaurar backup")
    else:
        criar_backup()

    print("\n" + "="*70 + "\n")
