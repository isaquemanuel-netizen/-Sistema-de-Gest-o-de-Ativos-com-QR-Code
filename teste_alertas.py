#!/usr/bin/env python3
"""
Script de teste para verificar o sistema de alertas por email
"""

import sqlite3
import email_service
from datetime import datetime, timedelta

DB = "ativos.db"

def criar_ativo_teste():
    """Cria um ativo de teste e tenta enviar notificação"""
    print("\n" + "="*60)
    print("  TESTE DE ALERTAS - NOVO ATIVO")
    print("="*60 + "\n")

    try:
        with sqlite3.connect(DB) as conn:
            cursor = conn.cursor()

            # Criar ativo de teste
            cursor.execute('''
                INSERT INTO ativos (codigo_id, nome, sn, descricao, localizacao, responsavel, estado)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', ('TEST-001', 'Notebook de Teste', 'SN-TEST-123',
                  'Equipamento criado para testar notificações automáticas',
                  'Sala TI', 'Isaque Manuel', 'Ativo'))

            ativo_id = cursor.lastrowid
            conn.commit()

            print(f"✓ Ativo de teste criado com ID: {ativo_id}")
            print(f"  Código: TEST-001")
            print(f"  Nome: Notebook de Teste\n")

        # Tentar enviar notificação
        print("📧 Tentando enviar email de notificação...\n")

        sucesso = email_service.notificar_novo_ativo({
            'ativo_id': ativo_id,
            'codigo_id': 'TEST-001',
            'nome': 'Notebook de Teste',
            'sn': 'SN-TEST-123',
            'localizacao': 'Sala TI',
            'responsavel': 'Isaque Manuel',
            'estado': 'Ativo'
        })

        if sucesso:
            print("✅ Email enviado com sucesso!")
            print("   Verifique sua caixa de entrada: isaque.manuel@tropigalia.co.mz\n")
        else:
            print("⚠️  Email não foi enviado")
            print("   Verifique a configuração SMTP no arquivo .env\n")

        return ativo_id

    except Exception as e:
        print(f"❌ Erro: {str(e)}\n")
        return None


def criar_ativo_com_garantia_vencendo():
    """Cria ativo com garantia vencendo em 15 dias"""
    print("\n" + "="*60)
    print("  TESTE DE ALERTAS - GARANTIA VENCENDO")
    print("="*60 + "\n")

    try:
        data_garantia = (datetime.now() + timedelta(days=15)).strftime('%Y-%m-%d')

        with sqlite3.connect(DB) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO ativos (codigo_id, nome, sn, descricao, localizacao, responsavel,
                                  estado, garantia_ate)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', ('TEST-002', 'Impressora com Garantia Vencendo', 'SN-IMP-456',
                  'Equipamento para testar alerta de garantia',
                  'Recepção', 'Isaque Manuel', 'Ativo', data_garantia))

            ativo_id = cursor.lastrowid
            conn.commit()

            print(f"✓ Ativo criado com garantia vencendo em 15 dias")
            print(f"  ID: {ativo_id}")
            print(f"  Garantia até: {data_garantia}\n")

        return ativo_id

    except Exception as e:
        print(f"❌ Erro: {str(e)}\n")
        return None


def criar_manutencao_proxima():
    """Cria manutenção agendada para daqui 3 dias"""
    print("\n" + "="*60)
    print("  TESTE DE ALERTAS - MANUTENÇÃO PRÓXIMA")
    print("="*60 + "\n")

    try:
        with sqlite3.connect(DB) as conn:
            cursor = conn.cursor()

            # Pegar um ativo existente
            ativo = cursor.execute('SELECT id, nome FROM ativos LIMIT 1').fetchone()

            if not ativo:
                print("⚠️  Nenhum ativo encontrado para criar manutenção")
                return None

            ativo_id, ativo_nome = ativo
            data_manutencao = (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')

            cursor.execute('''
                INSERT INTO manutencoes (ativo_id, tipo, descricao, data_manutencao,
                                       proximo_agendamento, responsavel, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (ativo_id, 'Preventiva', 'Limpeza e atualização de sistema',
                  datetime.now().strftime('%Y-%m-%d'), data_manutencao,
                  'Isaque Manuel', 'Agendada'))

            manutencao_id = cursor.lastrowid
            conn.commit()

            print(f"✓ Manutenção criada para daqui 3 dias")
            print(f"  Ativo: {ativo_nome}")
            print(f"  Agendada para: {data_manutencao}\n")

        return manutencao_id

    except Exception as e:
        print(f"❌ Erro: {str(e)}\n")
        return None


def testar_verificacao_manual():
    """Testa verificação manual de garantias e manutenções"""
    print("\n" + "="*60)
    print("  TESTE DE VERIFICAÇÃO MANUAL")
    print("="*60 + "\n")

    print("1. Verificando garantias vencendo (próximos 30 dias)...")
    garantias = email_service.verificar_garantias_vencendo(30)
    print(f"   → Encontradas: {len(garantias)} garantia(s)\n")

    if garantias:
        for g in garantias:
            print(f"   • {g[1]} - {g[2]} (vence em {g[5]} dias)")
        print()

    print("2. Verificando manutenções agendadas (próximos 7 dias)...")
    manutencoes = email_service.verificar_manutencoes_proximas(7)
    print(f"   → Encontradas: {len(manutencoes)} manutenção(ões)\n")

    if manutencoes:
        for m in manutencoes:
            print(f"   • {m[3]} - {m[4]} ({m[2]}) - em {m[6]} dias")
        print()

    if garantias or manutencoes:
        print("📧 Tentando enviar alertas por email...\n")

        if garantias:
            sucesso_g = email_service.enviar_alerta_garantias()
            if sucesso_g:
                print("   ✅ Alerta de garantias enviado!")
            else:
                print("   ⚠️  Alerta de garantias não enviado (verifique configuração SMTP)")

        if manutencoes:
            sucesso_m = email_service.enviar_alerta_manutencoes()
            if sucesso_m:
                print("   ✅ Alerta de manutenções enviado!")
            else:
                print("   ⚠️  Alerta de manutenções não enviado (verifique configuração SMTP)")
    else:
        print("ℹ️  Nenhum alerta pendente no momento")

    print()


def verificar_configuracao():
    """Verifica a configuração atual de email"""
    print("\n" + "="*60)
    print("  CONFIGURAÇÃO DE EMAIL")
    print("="*60 + "\n")

    config = email_service.get_configuracao_email()

    print(f"Servidor SMTP: {config['smtp_server']}:{config['smtp_port']}")
    print(f"Usuário: {config['smtp_user']}")
    print(f"Email From: {config['email_from']}")
    print(f"Destinatários: {', '.join(config['destinatarios']) if config['destinatarios'][0] else 'Não configurado'}")
    print(f"Alertas Habilitados: {'✅ SIM' if config['alertas_habilitados'] else '❌ NÃO'}")
    print()

    if not config['alertas_habilitados']:
        print("⚠️  ATENÇÃO: Alertas estão DESABILITADOS")
        print("   Configure ALERTAS_EMAIL=true no arquivo .env\n")

    if not config['smtp_user'] or config['smtp_user'] == '':
        print("⚠️  ATENÇÃO: Credenciais SMTP não configuradas")
        print("   Preencha SMTP_USER e SMTP_PASSWORD no arquivo .env\n")


if __name__ == '__main__':
    print("\n" + "🧪 " + "="*57)
    print("   TESTE COMPLETO DO SISTEMA DE ALERTAS POR EMAIL")
    print("   " + "="*57)

    # Verificar configuração
    verificar_configuracao()

    # Teste 1: Criar ativo e enviar notificação
    ativo_id = criar_ativo_teste()

    # Teste 2: Criar ativo com garantia vencendo
    criar_ativo_com_garantia_vencendo()

    # Teste 3: Criar manutenção próxima
    criar_manutencao_proxima()

    # Teste 4: Verificação manual
    testar_verificacao_manual()

    print("="*60)
    print("  TESTES CONCLUÍDOS")
    print("="*60)
    print("\n📋 PRÓXIMOS PASSOS:\n")
    print("1. Configure a senha SMTP no arquivo .env")
    print("2. Reinicie o Docker: docker-compose down && docker-compose up -d")
    print("3. Acesse http://localhost:5000/alertas para testar")
    print("4. Verifique seu email: isaque.manuel@tropigalia.co.mz\n")
