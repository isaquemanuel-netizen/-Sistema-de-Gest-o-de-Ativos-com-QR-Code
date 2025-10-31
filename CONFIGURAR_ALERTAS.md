# 📧 Configuração de Alertas Automáticos por Email

## ✅ Sistema Implementado e Funcionando!

Seu sistema está configurado para enviar emails automáticos para **isaque.manuel@tropigalia.co.mz** em todas estas situações:

### 🔔 Alertas Automáticos Implementados:

1. **📦 Novo Ativo Criado** - Email imediato ao cadastrar
2. **✏️ Ativo Editado** - Email imediato ao atualizar
3. **🗑️ Ativo Deletado** - Email imediato ao excluir
4. **🔧 Manutenção Adicionada** - Email imediato ao registrar manutenção
5. **⚠️ Garantias Vencendo** - Verificação diária automática (30 dias antes)
6. **📅 Manutenções Agendadas** - Verificação diária automática (7 dias antes)

---

## ⚙️ PASSO 1: Configurar Credenciais SMTP

Você precisa configurar a senha SMTP no arquivo `.env` que já foi criado.

### Abra o arquivo `.env` e preencha:

```env
SMTP_PASSWORD=PREENCHA_AQUI_SUA_SENHA
```

### Opções de Configuração SMTP:

#### **Opção A: Usar Gmail**
1. **Servidor**: `smtp.gmail.com` (já configurado)
2. **Porta**: `587` (já configurado)
3. **Email**: `isaque.manuel@tropigalia.co.mz` (já configurado)
4. **Senha**: Você precisa criar uma **"Senha de App"**

**Como criar Senha de App no Gmail:**
1. Acesse: https://myaccount.google.com/security
2. Ative "Verificação em 2 etapas" (se ainda não estiver ativo)
3. Vá em "Senhas de app"
4. Selecione "Email" como app
5. Copie a senha gerada (16 caracteres)
6. Cole no `.env` em `SMTP_PASSWORD=`

#### **Opção B: Usar Office365/Outlook**

Se seu email `@tropigalia.co.mz` usa Office365, configure:

```env
SMTP_SERVER=smtp.office365.com
SMTP_PORT=587
SMTP_USER=isaque.manuel@tropigalia.co.mz
SMTP_PASSWORD=sua_senha_normal_do_email
EMAIL_FROM=isaque.manuel@tropigalia.co.mz
```

---

## 🔄 PASSO 2: Reiniciar o Sistema

Após configurar a senha no `.env`, reinicie o Docker:

```bash
cd C:\Users\isaque.manuel\Desktop\sistema_ativos_qr
docker-compose down
docker-compose up -d
```

---

## 🧪 PASSO 3: Testar

### Teste pela Interface Web:

1. **Acesse:** http://localhost:5000/alertas
2. **Preencha seu email** no formulário de teste
3. **Clique em** "Enviar Email de Teste"
4. **Verifique sua caixa de entrada**

### Teste Criando um Ativo:

1. Acesse: http://localhost:5000/novo
2. Cadastre um novo ativo
3. Você receberá um email automático! 📧

---

## 📊 Scheduler Automático Configurado

O sistema está com scheduler ativo que verifica automaticamente:

- ✅ **Diariamente às 9h00**
- ✅ Garantias vencendo nos próximos 30 dias
- ✅ Manutenções agendadas nos próximos 7 dias

**Não precisa fazer nada!** Os alertas serão enviados automaticamente.

---

## 🔍 Verificar Status do Scheduler

Para ver se o scheduler está funcionando, veja os logs:

```bash
docker logs sistema_ativos_qr
```

Você deve ver:
```
✅ Scheduler de alertas automáticos iniciado
   → Verificações diárias às 9h00
   → Alertas de garantias (30 dias)
   → Alertas de manutenções (7 dias)
```

---

## 📋 Resumo dos Emails que Você Receberá

| Ação no Sistema | Email Enviado | Quando |
|-----------------|---------------|--------|
| Cadastrar novo ativo | 📦 Novo Ativo | Imediato |
| Editar ativo | ✏️ Ativo Atualizado | Imediato |
| Deletar ativo | 🗑️ Ativo Deletado | Imediato |
| Adicionar manutenção | 🔧 Nova Manutenção | Imediato |
| Garantia vencendo | ⚠️ Alerta de Garantia | Diário 9h |
| Manutenção próxima | 📅 Lembrete de Manutenção | Diário 9h |

---

## 🛠️ Solução de Problemas

### Email não está sendo enviado?

1. **Verifique o arquivo `.env`:**
   - Senha preenchida?
   - Servidor correto?
   - Email correto?

2. **Teste pela interface web:**
   - http://localhost:5000/alertas
   - Envie email de teste
   - Veja a mensagem de erro (se houver)

3. **Verifique os logs:**
   ```bash
   docker logs sistema_ativos_qr
   ```

### Gmail: "Senha incorreta"?

- Você precisa usar uma **Senha de App**, não a senha normal
- Acesse: https://myaccount.google.com/security
- Crie uma nova senha de app

### Office365: "Autenticação falhou"?

- Verifique se SMTP está habilitado na sua conta
- Use a senha normal do email
- Porta deve ser 587
- Servidor: `smtp.office365.com`

---

## ✅ Tudo Pronto!

Assim que você configurar a senha SMTP, o sistema começará a enviar emails automaticamente para **isaque.manuel@tropigalia.co.mz** em todas as ações importantes!

**Qualquer dúvida, verifique os logs ou acesse a página de alertas:** http://localhost:5000/alertas
