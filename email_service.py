"""
Serviço de Email para Sistema de Gestão de Ativos
Envia alertas sobre garantias, manutenções e outros eventos
"""

import sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import os

DB = "ativos.db"

# Configurações de email (podem ser sobrescritas por variáveis de ambiente)
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USER = os.getenv('SMTP_USER', '')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
EMAIL_FROM = os.getenv('EMAIL_FROM', SMTP_USER)
ALERTAS_HABILITADOS = os.getenv('ALERTAS_EMAIL', 'False').lower() == 'true'

# Lista de destinatários para alertas
DESTINATARIOS_ALERTAS = os.getenv('ALERTAS_DESTINATARIOS', '').split(',')


def get_configuracao_email():
    """Retorna configuração atual de email"""
    return {
        'smtp_server': SMTP_SERVER,
        'smtp_port': SMTP_PORT,
        'smtp_user': SMTP_USER,
        'email_from': EMAIL_FROM,
        'alertas_habilitados': ALERTAS_HABILITADOS,
        'destinatarios': DESTINATARIOS_ALERTAS
    }


def enviar_email(destinatarios, assunto, corpo_html, corpo_texto=None):
    """
    Envia email usando configurações SMTP

    Args:
        destinatarios: Lista de emails ou string única
        assunto: Assunto do email
        corpo_html: Corpo do email em HTML
        corpo_texto: Corpo alternativo em texto plano

    Returns:
        True se enviado com sucesso, False caso contrário
    """
    if not ALERTAS_HABILITADOS:
        print("⚠ Alertas por email desabilitados")
        return False

    if not SMTP_USER or not SMTP_PASSWORD:
        print("⚠ Credenciais SMTP não configuradas")
        return False

    # Garantir que destinatarios seja uma lista
    if isinstance(destinatarios, str):
        destinatarios = [destinatarios]

    # Filtrar emails vazios
    destinatarios = [d.strip() for d in destinatarios if d.strip()]

    if not destinatarios:
        print("⚠ Nenhum destinatário válido")
        return False

    try:
        # Criar mensagem
        msg = MIMEMultipart('alternative')
        msg['Subject'] = assunto
        msg['From'] = EMAIL_FROM
        msg['To'] = ', '.join(destinatarios)

        # Adicionar corpo texto plano
        if corpo_texto:
            part1 = MIMEText(corpo_texto, 'plain', 'utf-8')
            msg.attach(part1)

        # Adicionar corpo HTML
        part2 = MIMEText(corpo_html, 'html', 'utf-8')
        msg.attach(part2)

        # Conectar ao servidor SMTP
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)

        print(f"✓ Email enviado para: {', '.join(destinatarios)}")
        return True

    except Exception as e:
        print(f"✗ Erro ao enviar email: {str(e)}")
        return False


def criar_email_alerta_garantia(ativos_vencendo):
    """Cria HTML para alerta de garantias vencendo"""
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .header {{ background-color: #f39c12; color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 20px; }}
            .ativo {{ background-color: #f8f9fa; padding: 15px; margin: 10px 0; border-left: 4px solid #f39c12; }}
            .footer {{ background-color: #34495e; color: white; padding: 15px; text-align: center; font-size: 12px; }}
            .urgente {{ color: #e74c3c; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h2>⚠️ Alerta: Garantias Vencendo</h2>
        </div>
        <div class="content">
            <p>Os seguintes ativos têm garantia vencendo nos próximos 30 dias:</p>

            {''.join([f'''
            <div class="ativo">
                <strong>{ativo[1]} - {ativo[2]}</strong><br>
                <strong>Número de Série:</strong> {ativo[3]}<br>
                <strong>Garantia até:</strong> {ativo[4]}
                <span class="urgente">(Vence em {ativo[5]} dias)</span><br>
                <strong>Responsável:</strong> {ativo[6]}
            </div>
            ''' for ativo in ativos_vencendo])}

            <p><strong>Ação Recomendada:</strong> Verifique se é necessário renovar as garantias ou fazer backup dos equipamentos.</p>
        </div>
        <div class="footer">
            Sistema de Gestão de Ativos | Gerado automaticamente em {datetime.now().strftime('%d/%m/%Y %H:%M')}
        </div>
    </body>
    </html>
    """

    texto = f"""
    ALERTA: GARANTIAS VENCENDO

    Os seguintes ativos têm garantia vencendo nos próximos 30 dias:

    {chr(10).join([f"- {ativo[1]} - {ativo[2]} | SN: {ativo[3]} | Garantia até: {ativo[4]} (Vence em {ativo[5]} dias)" for ativo in ativos_vencendo])}

    Ação Recomendada: Verifique se é necessário renovar as garantias.

    ---
    Sistema de Gestão de Ativos
    Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}
    """

    return html, texto


def criar_email_alerta_manutencao(manutencoes_proximas):
    """Cria HTML para alerta de manutenções agendadas"""
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .header {{ background-color: #3498db; color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 20px; }}
            .manutencao {{ background-color: #e8f4f8; padding: 15px; margin: 10px 0; border-left: 4px solid #3498db; }}
            .footer {{ background-color: #34495e; color: white; padding: 15px; text-align: center; font-size: 12px; }}
            .badge {{ display: inline-block; padding: 5px 10px; border-radius: 3px; font-size: 11px; font-weight: bold; }}
            .preventiva {{ background-color: #2ecc71; color: white; }}
            .corretiva {{ background-color: #e74c3c; color: white; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h2>🔧 Lembrete: Manutenções Agendadas</h2>
        </div>
        <div class="content">
            <p>As seguintes manutenções estão agendadas para os próximos 7 dias:</p>

            {''.join([f'''
            <div class="manutencao">
                <strong>{man[3]} - {man[4]}</strong><br>
                <span class="badge {man[2].lower()}">{man[2]}</span><br>
                <strong>Agendada para:</strong> {man[5]} (em {man[6]} dias)<br>
                <strong>Descrição:</strong> {man[7] if man[7] else 'N/A'}<br>
                <strong>Responsável:</strong> {man[8] if man[8] else 'Não atribuído'}
            </div>
            ''' for man in manutencoes_proximas])}

            <p><strong>Ação Recomendada:</strong> Prepare os recursos necessários e contate os responsáveis.</p>
        </div>
        <div class="footer">
            Sistema de Gestão de Ativos | Gerado automaticamente em {datetime.now().strftime('%d/%m/%Y %H:%M')}
        </div>
    </body>
    </html>
    """

    texto = f"""
    LEMBRETE: MANUTENÇÕES AGENDADAS

    As seguintes manutenções estão agendadas para os próximos 7 dias:

    {chr(10).join([f"- {man[3]} - {man[4]} | Tipo: {man[2]} | Data: {man[5]} (em {man[6]} dias) | Responsável: {man[8] or 'Não atribuído'}" for man in manutencoes_proximas])}

    Ação Recomendada: Prepare os recursos necessários.

    ---
    Sistema de Gestão de Ativos
    Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}
    """

    return html, texto


def verificar_garantias_vencendo(dias=30):
    """
    Verifica ativos com garantia vencendo nos próximos X dias

    Args:
        dias: Número de dias para antecipar o alerta

    Returns:
        Lista de ativos com garantia vencendo
    """
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()

        ativos = cursor.execute('''
            SELECT id, codigo_id, nome, sn, garantia_ate,
                   CAST((julianday(garantia_ate) - julianday('now')) AS INTEGER) as dias_restantes,
                   responsavel
            FROM ativos
            WHERE garantia_ate IS NOT NULL
              AND garantia_ate > date('now')
              AND garantia_ate <= date('now', '+' || ? || ' days')
            ORDER BY garantia_ate ASC
        ''', (dias,)).fetchall()

    return ativos


def verificar_manutencoes_proximas(dias=7):
    """
    Verifica manutenções agendadas para os próximos X dias

    Args:
        dias: Número de dias para antecipar o alerta

    Returns:
        Lista de manutenções agendadas
    """
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()

        manutencoes = cursor.execute('''
            SELECT m.id, m.ativo_id, m.tipo, a.codigo_id, a.nome, m.proximo_agendamento,
                   CAST((julianday(m.proximo_agendamento) - julianday('now')) AS INTEGER) as dias_restantes,
                   m.descricao, m.responsavel
            FROM manutencoes m
            JOIN ativos a ON m.ativo_id = a.id
            WHERE m.proximo_agendamento IS NOT NULL
              AND m.proximo_agendamento >= date('now')
              AND m.proximo_agendamento <= date('now', '+' || ? || ' days')
            ORDER BY m.proximo_agendamento ASC
        ''', (dias,)).fetchall()

    return manutencoes


def enviar_alerta_garantias(destinatarios=None):
    """Envia alerta sobre garantias vencendo"""
    ativos = verificar_garantias_vencendo(30)

    if not ativos:
        print("✓ Nenhuma garantia vencendo nos próximos 30 dias")
        return False

    if destinatarios is None:
        destinatarios = DESTINATARIOS_ALERTAS

    html, texto = criar_email_alerta_garantia(ativos)
    assunto = f"⚠️ Alerta: {len(ativos)} garantia(s) vencendo nos próximos 30 dias"

    return enviar_email(destinatarios, assunto, html, texto)


def enviar_alerta_manutencoes(destinatarios=None):
    """Envia alerta sobre manutenções agendadas"""
    manutencoes = verificar_manutencoes_proximas(7)

    if not manutencoes:
        print("✓ Nenhuma manutenção agendada para os próximos 7 dias")
        return False

    if destinatarios is None:
        destinatarios = DESTINATARIOS_ALERTAS

    html, texto = criar_email_alerta_manutencao(manutencoes)
    assunto = f"🔧 Lembrete: {len(manutencoes)} manutenção(ões) agendada(s) para os próximos 7 dias"

    return enviar_email(destinatarios, assunto, html, texto)


def enviar_email_teste(destinatario):
    """Envia email de teste para verificar configuração"""
    html = """
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; padding: 20px; }
            .header { background-color: #2ecc71; color: white; padding: 20px; text-align: center; border-radius: 5px; }
            .content { padding: 20px; line-height: 1.6; }
        </style>
    </head>
    <body>
        <div class="header">
            <h2>✅ Email de Teste - Sistema de Ativos</h2>
        </div>
        <div class="content">
            <p>Se você está recebendo este email, significa que a configuração SMTP está funcionando corretamente!</p>
            <p><strong>Configuração atual:</strong></p>
            <ul>
                <li>Servidor SMTP: {smtp_server}</li>
                <li>Porta: {smtp_port}</li>
                <li>Remetente: {email_from}</li>
            </ul>
            <p>Você pode agora receber alertas sobre:</p>
            <ul>
                <li>🔔 Garantias vencendo</li>
                <li>🔧 Manutenções agendadas</li>
                <li>📦 Novos ativos cadastrados</li>
            </ul>
        </div>
    </body>
    </html>
    """.format(smtp_server=SMTP_SERVER, smtp_port=SMTP_PORT, email_from=EMAIL_FROM)

    texto = f"""
    EMAIL DE TESTE - Sistema de Ativos

    Se você está recebendo este email, a configuração SMTP está funcionando!

    Servidor: {SMTP_SERVER}:{SMTP_PORT}
    Remetente: {EMAIL_FROM}

    Você receberá alertas sobre garantias, manutenções e novos ativos.
    """

    return enviar_email(destinatario, "✅ Teste de Email - Sistema de Ativos", html, texto)


def executar_verificacao_alertas():
    """
    Executa verificação de todos os alertas e envia emails necessários
    Deve ser chamado periodicamente (ex: via cron job ou scheduler)
    """
    print(f"\n{'='*60}")
    print(f"  VERIFICAÇÃO DE ALERTAS - {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print(f"{'='*60}\n")

    if not ALERTAS_HABILITADOS:
        print("⚠ Sistema de alertas desabilitado")
        print("   Configure ALERTAS_EMAIL=true no .env\n")
        return

    # Verificar garantias
    print("1. Verificando garantias vencendo...")
    enviar_alerta_garantias()

    # Verificar manutenções
    print("\n2. Verificando manutenções agendadas...")
    enviar_alerta_manutencoes()

    print(f"\n{'='*60}")
    print("  VERIFICAÇÃO CONCLUÍDA")
    print(f"{'='*60}\n")


def notificar_novo_ativo(ativo_dados):
    """Envia notificação quando um novo ativo é criado"""
    if not ALERTAS_HABILITADOS:
        return False

    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .header {{ background-color: #2ecc71; color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 20px; }}
            .ativo {{ background-color: #e8f8f5; padding: 15px; margin: 10px 0; border-left: 4px solid #2ecc71; }}
            .footer {{ background-color: #34495e; color: white; padding: 15px; text-align: center; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h2>📦 Novo Ativo Cadastrado</h2>
        </div>
        <div class="content">
            <p>Um novo ativo foi cadastrado no sistema:</p>
            <div class="ativo">
                <strong>Código:</strong> {ativo_dados.get('codigo_id')}<br>
                <strong>Nome:</strong> {ativo_dados.get('nome')}<br>
                <strong>Série:</strong> {ativo_dados.get('sn')}<br>
                <strong>Localização:</strong> {ativo_dados.get('localizacao')}<br>
                <strong>Responsável:</strong> {ativo_dados.get('responsavel')}<br>
                <strong>Estado:</strong> {ativo_dados.get('estado')}
            </div>
            <p><a href="{BASE_URL}/ativo/{ativo_dados.get('ativo_id')}" style="color: #2ecc71; font-weight: bold;">Ver Detalhes do Ativo</a></p>
        </div>
        <div class="footer">
            Sistema de Gestão de Ativos | {datetime.now().strftime('%d/%m/%Y %H:%M')}
        </div>
    </body>
    </html>
    """

    texto = f"""
NOVO ATIVO CADASTRADO

Código: {ativo_dados.get('codigo_id')}
Nome: {ativo_dados.get('nome')}
Série: {ativo_dados.get('sn')}
Localização: {ativo_dados.get('localizacao')}
Responsável: {ativo_dados.get('responsavel')}
Estado: {ativo_dados.get('estado')}

Acesse: {BASE_URL}/ativo/{ativo_dados.get('ativo_id')}

---
Sistema de Gestão de Ativos | {datetime.now().strftime('%d/%m/%Y %H:%M')}
    """

    return enviar_email(
        DESTINATARIOS_ALERTAS,
        f"📦 Novo Ativo: {ativo_dados.get('nome')}",
        html,
        texto
    )


def notificar_ativo_editado(ativo_dados):
    """Envia notificação quando um ativo é editado"""
    if not ALERTAS_HABILITADOS:
        return False

    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .header {{ background-color: #3498db; color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 20px; }}
            .ativo {{ background-color: #ebf5fb; padding: 15px; margin: 10px 0; border-left: 4px solid #3498db; }}
            .footer {{ background-color: #34495e; color: white; padding: 15px; text-align: center; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h2>✏️ Ativo Atualizado</h2>
        </div>
        <div class="content">
            <p>O ativo <strong>{ativo_dados.get('nome')}</strong> foi atualizado:</p>
            <div class="ativo">
                <strong>Código:</strong> {ativo_dados.get('codigo_id')}<br>
                <strong>Nome:</strong> {ativo_dados.get('nome')}<br>
                <strong>Estado:</strong> {ativo_dados.get('estado')}
            </div>
            <p><a href="{BASE_URL}/ativo/{ativo_dados.get('ativo_id')}" style="color: #3498db; font-weight: bold;">Ver Detalhes do Ativo</a></p>
        </div>
        <div class="footer">
            Sistema de Gestão de Ativos | {datetime.now().strftime('%d/%m/%Y %H:%M')}
        </div>
    </body>
    </html>
    """

    texto = f"""
ATIVO ATUALIZADO

Código: {ativo_dados.get('codigo_id')}
Nome: {ativo_dados.get('nome')}
Estado: {ativo_dados.get('estado')}

Acesse: {BASE_URL}/ativo/{ativo_dados.get('ativo_id')}

---
Sistema de Gestão de Ativos | {datetime.now().strftime('%d/%m/%Y %H:%M')}
    """

    return enviar_email(
        DESTINATARIOS_ALERTAS,
        f"✏️ Ativo Atualizado: {ativo_dados.get('nome')}",
        html,
        texto
    )


def notificar_ativo_deletado(ativo_dados):
    """Envia notificação quando um ativo é deletado"""
    if not ALERTAS_HABILITADOS:
        return False

    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .header {{ background-color: #e74c3c; color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 20px; }}
            .ativo {{ background-color: #fadbd8; padding: 15px; margin: 10px 0; border-left: 4px solid #e74c3c; }}
            .footer {{ background-color: #34495e; color: white; padding: 15px; text-align: center; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h2>🗑️ Ativo Deletado</h2>
        </div>
        <div class="content">
            <p>O ativo <strong>{ativo_dados.get('nome')}</strong> foi removido do sistema:</p>
            <div class="ativo">
                <strong>Código:</strong> {ativo_dados.get('codigo_id')}<br>
                <strong>Nome:</strong> {ativo_dados.get('nome')}<br>
                <strong>Série:</strong> {ativo_dados.get('sn')}
            </div>
            <p style="color: #e74c3c;"><strong>Esta ação não pode ser desfeita.</strong></p>
        </div>
        <div class="footer">
            Sistema de Gestão de Ativos | {datetime.now().strftime('%d/%m/%Y %H:%M')}
        </div>
    </body>
    </html>
    """

    texto = f"""
ATIVO DELETADO

Código: {ativo_dados.get('codigo_id')}
Nome: {ativo_dados.get('nome')}
Série: {ativo_dados.get('sn')}

ATENÇÃO: Esta ação não pode ser desfeita.

---
Sistema de Gestão de Ativos | {datetime.now().strftime('%d/%m/%Y %H:%M')}
    """

    return enviar_email(
        DESTINATARIOS_ALERTAS,
        f"🗑️ Ativo Deletado: {ativo_dados.get('nome')}",
        html,
        texto
    )


def notificar_manutencao_adicionada(manutencao_dados):
    """Envia notificação quando uma manutenção é adicionada"""
    if not ALERTAS_HABILITADOS:
        return False

    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .header {{ background-color: #f39c12; color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 20px; }}
            .manutencao {{ background-color: #fef5e7; padding: 15px; margin: 10px 0; border-left: 4px solid #f39c12; }}
            .footer {{ background-color: #34495e; color: white; padding: 15px; text-align: center; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h2>🔧 Nova Manutenção Registrada</h2>
        </div>
        <div class="content">
            <p>Uma nova manutenção foi registrada:</p>
            <div class="manutencao">
                <strong>Ativo:</strong> {manutencao_dados.get('ativo_nome')}<br>
                <strong>Tipo:</strong> {manutencao_dados.get('tipo')}<br>
                <strong>Data:</strong> {manutencao_dados.get('data_manutencao')}<br>
                <strong>Descrição:</strong> {manutencao_dados.get('descricao')}<br>
                <strong>Responsável:</strong> {manutencao_dados.get('responsavel', 'Não informado')}
                {f"<br><strong>Próximo Agendamento:</strong> {manutencao_dados.get('proximo_agendamento')}" if manutencao_dados.get('proximo_agendamento') else ""}
            </div>
            <p><a href="{BASE_URL}/ativo/{manutencao_dados.get('ativo_id')}" style="color: #f39c12; font-weight: bold;">Ver Ativo</a></p>
        </div>
        <div class="footer">
            Sistema de Gestão de Ativos | {datetime.now().strftime('%d/%m/%Y %H:%M')}
        </div>
    </body>
    </html>
    """

    texto = f"""
NOVA MANUTENÇÃO REGISTRADA

Ativo: {manutencao_dados.get('ativo_nome')}
Tipo: {manutencao_dados.get('tipo')}
Data: {manutencao_dados.get('data_manutencao')}
Descrição: {manutencao_dados.get('descricao')}
Responsável: {manutencao_dados.get('responsavel', 'Não informado')}
{f"Próximo Agendamento: {manutencao_dados.get('proximo_agendamento')}" if manutencao_dados.get('proximo_agendamento') else ""}

Acesse: {BASE_URL}/ativo/{manutencao_dados.get('ativo_id')}

---
Sistema de Gestão de Ativos | {datetime.now().strftime('%d/%m/%Y %H:%M')}
    """

    return enviar_email(
        DESTINATARIOS_ALERTAS,
        f"🔧 Nova Manutenção: {manutencao_dados.get('ativo_nome')} - {manutencao_dados.get('tipo')}",
        html,
        texto
    )


if __name__ == '__main__':
    # Executar verificação de alertas
    executar_verificacao_alertas()
