#!/usr/bin/env python3
"""
Script para regenerar todos os QR codes com o novo URL da rede
"""

import sqlite3
import qrcode
import os

DB = "ativos.db"
QR_FOLDER = "static/qrcodes"
BASE_URL = os.environ.get('BASE_URL', 'http://11.1.106.225:5000')

def regenerar_qrcodes():
    """Regenera todos os QR codes com o novo URL"""

    # Criar pasta se não existir
    os.makedirs(QR_FOLDER, exist_ok=True)

    # Conectar ao banco
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()

        # Buscar todos os ativos
        ativos = cursor.execute("SELECT id, codigo_id, nome FROM ativos").fetchall()

        if not ativos:
            print("Nenhum ativo encontrado no banco de dados.")
            return

        print(f"Regenerando QR codes para {len(ativos)} ativos...")
        print(f"Usando URL base: {BASE_URL}")
        print("-" * 60)

        # Regenerar QR code para cada ativo
        sucesso = 0
        erro = 0

        for ativo in ativos:
            ativo_id = ativo[0]
            codigo = ativo[1]
            nome = ativo[2]

            try:
                # Gerar URL completo
                url = f"{BASE_URL}/ver/{ativo_id}"

                # Criar QR code
                img = qrcode.make(url)

                # Salvar QR code
                qr_path = f"{QR_FOLDER}/ativo_{ativo_id}.png"
                img.save(qr_path)

                print(f"✓ QR Code regenerado: {codigo} - {nome}")
                sucesso += 1

            except Exception as e:
                print(f"✗ Erro ao regenerar QR code para {codigo}: {str(e)}")
                erro += 1

        print("-" * 60)
        print(f"\nResumo:")
        print(f"  Sucesso: {sucesso}")
        print(f"  Erros: {erro}")
        print(f"  Total: {len(ativos)}")

        if sucesso > 0:
            print(f"\n✓ QR codes regenerados com sucesso!")
            print(f"  Os QR codes agora apontam para: {BASE_URL}/ver/<id>")
            print(f"\n  Para testar, escaneie um QR code com seu celular")
            print(f"  conectado na mesma rede WiFi.")

if __name__ == '__main__':
    print("=" * 60)
    print("  REGENERAÇÃO DE QR CODES - Sistema de Gestão de Ativos")
    print("=" * 60)
    print()

    try:
        regenerar_qrcodes()
    except Exception as e:
        print(f"\n✗ Erro crítico: {str(e)}")
        exit(1)
