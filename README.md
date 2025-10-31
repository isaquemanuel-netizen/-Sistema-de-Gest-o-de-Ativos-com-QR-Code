# 🏢 Sistema de Gestão de Ativos com QR Code

Sistema completo para gerenciamento de ativos empresariais com QR Code, controle de manutenções, inventários e alertas automáticos.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Flask](https://img.shields.io/badge/Flask-3.0.0-green)
![Docker](https://img.shields.io/badge/Docker-Ready-blue)

## ✨ Funcionalidades Principais

- 🔐 Sistema de autenticação com controle de acesso por roles
- 📦 Gestão completa de ativos com QR Code
- 🔧 Controle de manutenções preventivas e corretivas
- 📊 Inventários físicos com checklist
- 📧 Alertas automáticos por email
- 💾 Backup automático do banco de dados
- 📱 PWA - Instalável como app
- 📝 Auditoria completa de ações

## 🚀 Instalação Rápida

```bash
docker-compose up --build -d
docker exec sistema_ativos_qr python create_users_table.py
```

Acesse: http://localhost:5000  
Login: admin / admin123

## 📚 Documentação Completa

Veja a documentação completa em [DOCS.md](DOCS.md)

## 👤 Autor

Isaque Manuel

## 📄 Licença

MIT License
