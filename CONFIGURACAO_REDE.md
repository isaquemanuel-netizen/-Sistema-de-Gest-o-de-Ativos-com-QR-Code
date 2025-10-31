# Configuração para Acesso na Rede Local

Este guia explica como configurar o Sistema de Gestão de Ativos para ser acessado por qualquer dispositivo na sua rede local.

## 📱 Objetivo

Permitir que QR codes sejam escaneados por celulares e outros dispositivos na mesma rede WiFi, exibindo as informações dos ativos.

---

## 🔧 Configuração

### 1. Descobrir o IP da sua máquina

No Windows, abra o Prompt de Comando e execute:

```bash
ipconfig
```

Procure por **IPv4 Address** na seção da sua conexão de rede ativa (Ethernet ou Wi-Fi).

**Exemplo:** `11.1.106.225`

---

### 2. Atualizar o arquivo `docker-compose.yml`

Edite o arquivo `docker-compose.yml` e atualize a variável `BASE_URL`:

```yaml
environment:
  - FLASK_APP=app.py
  - PYTHONUNBUFFERED=1
  - BASE_URL=http://SEU_IP_AQUI:5000  # ⬅️ Substitua pelo seu IP
```

**Exemplo:**
```yaml
  - BASE_URL=http://11.1.106.225:5000
```

---

### 3. Reiniciar o Docker

```bash
docker-compose down
docker-compose up --build -d
```

---

### 4. Regenerar os QR Codes

Após reiniciar o Docker, os novos ativos já terão QR codes com o IP correto.

Para atualizar os QR codes de ativos existentes, você tem 3 opções:

#### **Opção A: Pelo Dashboard (Recomendado)**

1. Acesse: `http://SEU_IP:5000/dashboard`
2. Na seção **Administração**, clique em **Regenerar QR Codes**
3. Confirme a ação

#### **Opção B: Script Python**

Execute o script de regeneração:

```bash
docker exec -it sistema_ativos_qr python regenerar_qrcodes.py
```

#### **Opção C: Manualmente via Python**

```bash
cd pasta_do_projeto
python regenerar_qrcodes.py
```

---

## ✅ Testar o Acesso

### 1. **Pelo navegador do PC:**

Abra: `http://SEU_IP:5000`

### 2. **Pelo celular:**

1. Conecte o celular na **mesma rede WiFi** que o PC
2. Abra o navegador e acesse: `http://SEU_IP:5000`
3. Teste escanear um QR code

---

## 🔥 Configurar Firewall (Se necessário)

Se não conseguir acessar de outros dispositivos, pode ser necessário liberar a porta 5000 no firewall:

### Windows Firewall:

```powershell
# Executar como Administrador
netsh advfirewall firewall add rule name="Flask Sistema Ativos" dir=in action=allow protocol=TCP localport=5000
```

Ou manualmente:
1. Pesquisar: "Firewall do Windows"
2. Clicar em "Configurações avançadas"
3. "Regras de Entrada" → "Nova Regra"
4. Tipo: Porta
5. Protocolo: TCP
6. Porta: 5000
7. Permitir a conexão
8. Aplicar a todos os perfis

---

## 📝 Notas Importantes

### IP Dinâmico

Se o seu IP mudar (comum em redes com DHCP):

1. Descubra o novo IP com `ipconfig`
2. Atualize o `docker-compose.yml`
3. Reinicie o Docker
4. Regenere os QR codes

### IP Estático (Recomendado para produção)

Para evitar mudanças de IP:

1. Configure um IP estático no roteador para o seu PC
2. Ou use um serviço de DNS local (como mDNS/Bonjour)

### Acesso Externo (Internet)

Este guia configura apenas para **rede local**. Para acesso pela internet, você precisaria:

- Configurar port forwarding no roteador
- Usar um serviço de DNS dinâmico
- **⚠️ IMPORTANTE:** Adicionar autenticação e HTTPS para segurança

---

## 🆘 Resolução de Problemas

### Não consigo acessar de outros dispositivos

1. ✓ Verifique se todos os dispositivos estão na mesma rede WiFi
2. ✓ Teste fazer ping para o IP do servidor: `ping SEU_IP`
3. ✓ Verifique se o Docker está rodando: `docker ps`
4. ✓ Verifique os logs: `docker logs sistema_ativos_qr`
5. ✓ Verifique o firewall (ver seção acima)

### QR codes não funcionam no celular

1. ✓ Verifique se regenerou os QR codes após mudar o IP
2. ✓ Escaneie o QR code e veja qual URL aparece
3. ✓ Teste acessar essa URL manualmente no navegador do celular

### Erro "Connection Refused"

1. ✓ Verifique se o Docker está rodando
2. ✓ Verifique se a porta 5000 está liberada
3. ✓ Tente reiniciar o Docker

---

## 📞 Informações Úteis

**IP Atual Configurado:** `11.1.106.225`

**Porta:** `5000`

**URL de Acesso:** `http://11.1.106.225:5000`

**URL dos QR Codes:** `http://11.1.106.225:5000/ver/<id>`

---

## 🎯 Exemplo de Uso

1. **Cadastrar um ativo** no sistema pelo PC
2. **QR code é gerado automaticamente** com URL da rede
3. **Imprimir etiqueta** com o QR code
4. **Colar no equipamento**
5. **Escanear com celular** para ver informações

---

## ✨ Dicas

- Mantenha o IP documentado
- Teste os QR codes antes de imprimir em lote
- Use a página de etiquetas para impressão otimizada
- Configure IP estático para evitar reconfigurações
