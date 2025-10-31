#!/usr/bin/env python3
"""
Gerador de Ícones PWA
Gera todos os tamanhos de ícones necessários para PWA a partir do logo
"""

from PIL import Image, ImageDraw, ImageFont
import os

# Tamanhos de ícones necessários para PWA
ICON_SIZES = [
    16, 32, 72, 96, 120, 128, 144, 152, 180, 192, 384, 512
]

# Diretórios
STATIC_DIR = os.path.join(os.path.dirname(__file__), 'static')
ICONS_DIR = os.path.join(STATIC_DIR, 'icons')
LOGO_PATH = os.path.join(STATIC_DIR, 'logo.png')

def create_icon_background(size, color='#1e40af'):
    """Cria um ícone com fundo colorido e texto"""
    # Criar imagem com fundo
    img = Image.new('RGB', (size, size), color)
    draw = ImageDraw.Draw(img)

    # Adicionar texto "AQ" (Ativos QR)
    text = "AQ"

    # Calcular tamanho da fonte
    font_size = int(size * 0.5)

    try:
        # Tentar usar uma fonte padrão
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        # Fallback para fonte padrão
        font = ImageFont.load_default()

    # Calcular posição central do texto
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    x = (size - text_width) // 2
    y = (size - text_height) // 2

    # Desenhar texto
    draw.text((x, y), text, fill='white', font=font)

    return img

def generate_icons():
    """Gera todos os ícones necessários"""

    # Criar diretório se não existir
    os.makedirs(ICONS_DIR, exist_ok=True)

    print("🎨 Gerando ícones PWA...")

    # Verificar se logo existe
    if os.path.exists(LOGO_PATH):
        print(f"✓ Logo encontrado: {LOGO_PATH}")
        try:
            base_img = Image.open(LOGO_PATH)
            print(f"✓ Logo carregado: {base_img.size}")
        except Exception as e:
            print(f"⚠ Erro ao carregar logo: {e}")
            print("  Gerando ícones com texto...")
            base_img = None
    else:
        print(f"⚠ Logo não encontrado em {LOGO_PATH}")
        print("  Gerando ícones com texto...")
        base_img = None

    # Gerar cada tamanho
    for size in ICON_SIZES:
        filename = f"icon-{size}x{size}.png"
        filepath = os.path.join(ICONS_DIR, filename)

        if base_img:
            # Redimensionar logo existente
            icon = base_img.copy()
            icon = icon.resize((size, size), Image.Resampling.LANCZOS)
        else:
            # Criar ícone com texto
            icon = create_icon_background(size)

        # Salvar
        icon.save(filepath, 'PNG')
        print(f"  ✓ Criado: {filename}")

    print(f"\n✅ {len(ICON_SIZES)} ícones criados com sucesso em: {ICONS_DIR}")

    # Criar também browserconfig.xml para Windows
    create_browserconfig()

def create_browserconfig():
    """Cria arquivo browserconfig.xml para Windows tiles"""

    browserconfig = '''<?xml version="1.0" encoding="utf-8"?>
<browserconfig>
    <msapplication>
        <tile>
            <square70x70logo src="/static/icons/icon-72x72.png"/>
            <square150x150logo src="/static/icons/icon-152x152.png"/>
            <square310x310logo src="/static/icons/icon-384x384.png"/>
            <TileColor>#1e40af</TileColor>
        </tile>
    </msapplication>
</browserconfig>
'''

    filepath = os.path.join(STATIC_DIR, 'browserconfig.xml')
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(browserconfig)

    print(f"✓ browserconfig.xml criado")

def create_offline_page():
    """Cria página offline para PWA"""

    offline_html = '''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Offline - Sistema de Ativos</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-align: center;
        }
        .container {
            max-width: 400px;
            padding: 2rem;
        }
        h1 {
            font-size: 3rem;
            margin-bottom: 1rem;
        }
        p {
            font-size: 1.25rem;
            opacity: 0.9;
        }
        button {
            margin-top: 2rem;
            padding: 1rem 2rem;
            font-size: 1rem;
            background: white;
            color: #667eea;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
        }
        button:hover {
            transform: scale(1.05);
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📴</h1>
        <h2>Você está offline</h2>
        <p>Não foi possível conectar ao servidor. Verifique sua conexão e tente novamente.</p>
        <button onclick="window.location.reload()">Tentar Novamente</button>
    </div>
</body>
</html>
'''

    templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
    filepath = os.path.join(templates_dir, 'offline.html')

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(offline_html)

    print(f"✓ offline.html criado")

if __name__ == '__main__':
    print("\n" + "="*60)
    print("  GERADOR DE ÍCONES PWA")
    print("  Sistema de Gestão de Ativos")
    print("="*60 + "\n")

    try:
        generate_icons()
        create_offline_page()

        print("\n" + "="*60)
        print("  ✅ PROCESSO CONCLUÍDO COM SUCESSO!")
        print("="*60)
        print("\n📋 Próximos passos:")
        print("  1. Rebuild Docker: docker-compose up --build -d")
        print("  2. Acesse: http://localhost:5000")
        print("  3. No navegador, procure o botão 'Instalar App'")
        print("  4. No Chrome: Menu → Instalar aplicativo")
        print("  5. No mobile: 'Adicionar à tela inicial'\n")

    except Exception as e:
        print(f"\n❌ Erro: {str(e)}")
        import traceback
        traceback.print_exc()
