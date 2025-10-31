from flask import Flask, render_template, request, redirect, url_for, send_file, flash, jsonify, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import qrcode
import os
import pandas as pd
from datetime import datetime
import email_service
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
import logging
from logging.handlers import RotatingFileHandler
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'sistema_ativos_secret_key_2024_CHANGE_IN_PRODUCTION')
app.config['PERMANENT_SESSION_LIFETIME'] = 1800  # 30 minutos
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'static/uploads'

DB = "ativos.db"
QR_FOLDER = "static/qrcodes"
BASE_URL = os.environ.get('BASE_URL', 'http://localhost:5000')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'xls', 'xlsx'}

# Configurar logging
if not os.path.exists('logs'):
    os.makedirs('logs')

logging.basicConfig(level=logging.INFO)
file_handler = RotatingFileHandler('logs/sistema_ativos.log', maxBytes=10240000, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)
app.logger.info('Sistema de Ativos iniciado')

os.makedirs(QR_FOLDER, exist_ok=True)
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'fotos'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'documentos'), exist_ok=True)

# Configurar Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'
login_manager.login_message_category = 'warning'

# Classe de Usuário
class User(UserMixin):
    def __init__(self, id, username, email, nome, perfil, ativo=True):
        self.id = id
        self.username = username
        self.email = email
        self.nome = nome
        self.perfil = perfil  # admin, gestor, visualizador, tecnico
        self.ativo = ativo

    def is_admin(self):
        return self.perfil == 'admin'

    def is_gestor(self):
        return self.perfil in ['admin', 'gestor']

    def can_edit(self):
        return self.perfil in ['admin', 'gestor', 'tecnico']

@login_manager.user_loader
def load_user(user_id):
    try:
        with sqlite3.connect(DB) as conn:
            user_data = conn.execute(
                'SELECT id, username, email, nome, perfil, ativo FROM usuarios WHERE id = ?',
                (user_id,)
            ).fetchone()

            if user_data and user_data[5]:  # ativo = True
                return User(user_data[0], user_data[1], user_data[2], user_data[3], user_data[4], user_data[5])
    except Exception as e:
        app.logger.error(f'Erro ao carregar usuário: {e}')
    return None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def registrar_historico(ativo_id, acao, campo=None, valor_anterior=None, valor_novo=None):
    try:
        usuario = current_user.username if current_user.is_authenticated else 'Sistema'
        with sqlite3.connect(DB) as conn:
            conn.execute('''
                INSERT INTO historico (ativo_id, acao, campo, valor_anterior, valor_novo, usuario, ip_address)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (ativo_id, acao, campo, valor_anterior, valor_novo, usuario, request.remote_addr))
            conn.commit()
    except Exception as e:
        print(f"Erro ao registrar histórico: {e}")

def init_db():
    with sqlite3.connect(DB) as conn:
        # Tabela principal de ativos
        conn.execute('''
            CREATE TABLE IF NOT EXISTS ativos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo_id TEXT,
                nome TEXT,
                sn TEXT,
                descricao TEXT,
                localizacao TEXT,
                responsavel TEXT,
                estado TEXT,
                categoria_id INTEGER,
                subcategoria TEXT,
                numero_patrimonio TEXT,
                data_aquisicao DATE,
                valor_aquisicao REAL,
                fornecedor TEXT,
                garantia_ate DATE,
                observacoes TEXT
            )
        ''')

        # Tabela de categorias
        conn.execute('''
            CREATE TABLE IF NOT EXISTS categorias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL UNIQUE,
                descricao TEXT,
                icone TEXT,
                cor TEXT,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Tabela de histórico/auditoria
        conn.execute('''
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

        # Tabela de anexos (fotos e documentos)
        conn.execute('''
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

        # Tabela de manutenções
        conn.execute('''
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

        # Tabela de inventários
        conn.execute('''
            CREATE TABLE IF NOT EXISTS inventarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT NOT NULL,
                descricao TEXT,
                tipo TEXT NOT NULL,
                filtro_categoria_id INTEGER,
                filtro_localizacao TEXT,
                filtro_responsavel TEXT,
                status TEXT DEFAULT 'Em Andamento',
                total_ativos INTEGER DEFAULT 0,
                total_conferidos INTEGER DEFAULT 0,
                total_nao_localizados INTEGER DEFAULT 0,
                iniciado_por TEXT DEFAULT 'Admin',
                data_inicio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_conclusao TIMESTAMP,
                observacoes TEXT,
                FOREIGN KEY (filtro_categoria_id) REFERENCES categorias (id)
            )
        ''')

        # Tabela de itens do inventário
        conn.execute('''
            CREATE TABLE IF NOT EXISTS inventario_itens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                inventario_id INTEGER NOT NULL,
                ativo_id INTEGER NOT NULL,
                status TEXT DEFAULT 'Pendente',
                observacao TEXT,
                conferido_por TEXT,
                data_conferencia TIMESTAMP,
                FOREIGN KEY (inventario_id) REFERENCES inventarios (id) ON DELETE CASCADE,
                FOREIGN KEY (ativo_id) REFERENCES ativos (id) ON DELETE CASCADE
            )
        ''')

        # Inserir categorias padrão se não existirem
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
                conn.execute('INSERT INTO categorias (nome, descricao, icone, cor) VALUES (?, ?, ?, ?)', cat)
            except sqlite3.IntegrityError:
                pass  # Categoria já existe

        conn.commit()

@app.route('/')
@login_required
def index():
    # Redireciona para o dashboard
    return redirect(url_for('dashboard'))

@app.route('/ativos')
@login_required
def ativos():
    busca = request.args.get('busca', '').strip()
    query = "SELECT * FROM ativos"
    params = ()

    if busca:
        busca_like = f"%{busca}%"
        query += """
            WHERE
                codigo_id LIKE ? OR
                nome LIKE ? OR
                sn LIKE ? OR
                descricao LIKE ? OR
                localizacao LIKE ? OR
                responsavel LIKE ?
        """
        params = (busca_like,) * 6

    with sqlite3.connect(DB) as conn:
        ativos_list = conn.execute(query, params).fetchall()

    return render_template('index.html', ativos=ativos_list, busca=busca)

@app.route('/novo')
@login_required
def novo():
    with sqlite3.connect(DB) as conn:
        categorias = conn.execute('SELECT id, nome, icone FROM categorias ORDER BY nome').fetchall()
    return render_template('novo.html', categorias=categorias)

@app.route('/add', methods=['POST'])
@login_required
def add():
    try:
        codigo_id = request.form['codigo_id']
        nome = request.form['nome']
        sn = request.form['sn']
        descricao = request.form['descricao']
        localizacao = request.form['localizacao']
        responsavel = request.form['responsavel']
        estado = request.form['estado']

        # Novos campos
        categoria_id = request.form.get('categoria_id') or None
        subcategoria = request.form.get('subcategoria') or None
        numero_patrimonio = request.form.get('numero_patrimonio') or None
        data_aquisicao = request.form.get('data_aquisicao') or None
        valor_aquisicao = request.form.get('valor_aquisicao') or None
        fornecedor = request.form.get('fornecedor') or None
        garantia_ate = request.form.get('garantia_ate') or None
        observacoes = request.form.get('observacoes') or None

        with sqlite3.connect(DB) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO ativos (codigo_id, nome, sn, descricao, localizacao, responsavel, estado,
                                  categoria_id, subcategoria, numero_patrimonio, data_aquisicao,
                                  valor_aquisicao, fornecedor, garantia_ate, observacoes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (codigo_id, nome, sn, descricao, localizacao, responsavel, estado,
                 categoria_id, subcategoria, numero_patrimonio, data_aquisicao,
                 valor_aquisicao, fornecedor, garantia_ate, observacoes))
            ativo_id = cursor.lastrowid
            conn.commit()

        # Gera QR Code com URL correta
        url = f"{BASE_URL}/ver/{ativo_id}"
        img = qrcode.make(url)
        img.save(f"{QR_FOLDER}/ativo_{ativo_id}.png")

        # Registrar no histórico
        registrar_historico(ativo_id, 'Ativo criado', None, None, f'{codigo_id} - {nome}')

        # Enviar notificação por email
        email_service.notificar_novo_ativo({
            'ativo_id': ativo_id,
            'codigo_id': codigo_id,
            'nome': nome,
            'sn': sn,
            'localizacao': localizacao,
            'responsavel': responsavel,
            'estado': estado
        })

        flash(f'Ativo "{nome}" cadastrado com sucesso!', 'success')
        return redirect(url_for('ativo', ativo_id=ativo_id))

    except Exception as e:
        flash(f'Erro ao cadastrar ativo: {str(e)}', 'error')
        return redirect(url_for('novo'))

@app.route('/ativo/<int:ativo_id>')
@login_required
def ativo(ativo_id):
    with sqlite3.connect(DB) as conn:
        # Dados do ativo
        ativo = conn.execute("SELECT * FROM ativos WHERE id=?", (ativo_id,)).fetchone()

        if not ativo:
            flash('Ativo não encontrado!', 'error')
            return redirect(url_for('ativos'))

        # Categoria do ativo
        categoria = None
        if len(ativo) > 8 and ativo[8]:  # categoria_id está na posição 8
            categoria = conn.execute("SELECT nome, icone, cor FROM categorias WHERE id=?", (ativo[8],)).fetchone()

        # Anexos (fotos e documentos)
        anexos = conn.execute('''
            SELECT id, tipo, nome_arquivo, caminho, tamanho, descricao, principal, criado_em
            FROM anexos
            WHERE ativo_id = ?
            ORDER BY principal DESC, criado_em DESC
        ''', (ativo_id,)).fetchall()

        # Separar fotos e documentos
        fotos = [a for a in anexos if a[1] == 'foto']
        documentos = [a for a in anexos if a[1] == 'documento']

        # Manutenções
        manutencoes = conn.execute('''
            SELECT id, tipo, descricao, data_manutencao, proximo_agendamento,
                   responsavel, custo, status, observacoes, criado_em
            FROM manutencoes
            WHERE ativo_id = ?
            ORDER BY data_manutencao DESC
        ''', (ativo_id,)).fetchall()

        # Histórico
        historico = conn.execute('''
            SELECT id, acao, campo, valor_anterior, valor_novo, usuario, ip_address, criado_em
            FROM historico
            WHERE ativo_id = ?
            ORDER BY criado_em DESC
            LIMIT 50
        ''', (ativo_id,)).fetchall()

        # Todas as categorias (para seleção)
        categorias = conn.execute('SELECT id, nome, icone FROM categorias ORDER BY nome').fetchall()

    return render_template('detalhe.html',
                         ativo=ativo,
                         categoria=categoria,
                         fotos=fotos,
                         documentos=documentos,
                         manutencoes=manutencoes,
                         historico=historico,
                         categorias=categorias)

@app.route('/editar/<int:ativo_id>', methods=['GET', 'POST'])
@login_required
def editar(ativo_id):
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()

        if request.method == 'POST':
            try:
                # Campos originais
                codigo_id = request.form['codigo_id']
                nome = request.form['nome']
                sn = request.form['sn']
                descricao = request.form['descricao']
                localizacao = request.form['localizacao']
                responsavel = request.form['responsavel']
                estado = request.form['estado']

                # Novos campos
                categoria_id = request.form.get('categoria_id') or None
                subcategoria = request.form.get('subcategoria') or None
                numero_patrimonio = request.form.get('numero_patrimonio') or None
                data_aquisicao = request.form.get('data_aquisicao') or None
                valor_aquisicao = request.form.get('valor_aquisicao') or None
                fornecedor = request.form.get('fornecedor') or None
                garantia_ate = request.form.get('garantia_ate') or None
                observacoes = request.form.get('observacoes') or None

                cursor.execute('''
                    UPDATE ativos SET
                        codigo_id = ?, nome = ?, sn = ?, descricao = ?,
                        localizacao = ?, responsavel = ?, estado = ?,
                        categoria_id = ?, subcategoria = ?, numero_patrimonio = ?,
                        data_aquisicao = ?, valor_aquisicao = ?, fornecedor = ?,
                        garantia_ate = ?, observacoes = ?
                    WHERE id = ?
                ''', (codigo_id, nome, sn, descricao, localizacao, responsavel, estado,
                     categoria_id, subcategoria, numero_patrimonio, data_aquisicao,
                     valor_aquisicao, fornecedor, garantia_ate, observacoes, ativo_id))
                conn.commit()

                # Registrar no histórico
                registrar_historico(ativo_id, 'editado')

                # Enviar notificação por email
                email_service.notificar_ativo_editado({
                    'ativo_id': ativo_id,
                    'codigo_id': codigo_id,
                    'nome': nome,
                    'estado': estado
                })

                flash(f'Ativo "{nome}" atualizado com sucesso!', 'success')
                return redirect(url_for('ativo', ativo_id=ativo_id))

            except Exception as e:
                flash(f'Erro ao atualizar ativo: {str(e)}', 'error')
                return redirect(url_for('editar', ativo_id=ativo_id))

        ativo = cursor.execute("SELECT * FROM ativos WHERE id=?", (ativo_id,)).fetchone()

        if not ativo:
            flash('Ativo não encontrado!', 'error')
            return redirect(url_for('ativos'))

        # Buscar categorias para o selector
        categorias = cursor.execute('SELECT id, nome, icone FROM categorias ORDER BY nome').fetchall()

    return render_template('editar.html', ativo=ativo, categorias=categorias)

@app.route('/deletar/<int:ativo_id>', methods=['POST'])
@login_required
def deletar(ativo_id):
    try:
        with sqlite3.connect(DB) as conn:
            # Busca dados do ativo antes de deletar
            ativo = conn.execute("SELECT codigo_id, nome, sn FROM ativos WHERE id=?", (ativo_id,)).fetchone()

            if ativo:
                codigo_id, nome_ativo, sn = ativo

                # Enviar notificação ANTES de deletar
                email_service.notificar_ativo_deletado({
                    'codigo_id': codigo_id,
                    'nome': nome_ativo,
                    'sn': sn
                })
            else:
                nome_ativo = "Ativo"

            conn.execute("DELETE FROM ativos WHERE id=?", (ativo_id,))
            conn.commit()

        # Remove o QR Code
        qr_path = os.path.join(QR_FOLDER, f"ativo_{ativo_id}.png")
        if os.path.exists(qr_path):
            os.remove(qr_path)

        flash(f'Ativo "{nome_ativo}" excluído com sucesso!', 'success')

    except Exception as e:
        flash(f'Erro ao excluir ativo: {str(e)}', 'error')

    return redirect(url_for('ativos'))

@app.route('/exportar')
@login_required
def exportar():
    try:
        with sqlite3.connect(DB) as conn:
            df = pd.read_sql_query("SELECT * FROM ativos", conn)

        if df.empty:
            flash('Não há ativos para exportar!', 'warning')
            return redirect(url_for('ativos'))

        file_path = "ativos.xlsx"
        df.to_excel(file_path, index=False)

        return send_file(file_path, as_attachment=True, download_name='ativos_export.xlsx')

    except Exception as e:
        flash(f'Erro ao exportar ativos: {str(e)}', 'error')
        return redirect(url_for('ativos'))

@app.route('/ver/<int:ativo_id>')
@login_required
def ver(ativo_id):
    with sqlite3.connect(DB) as conn:
        ativo = conn.execute("SELECT * FROM ativos WHERE id=?", (ativo_id,)).fetchone()
    return render_template('visualizar.html', ativo=ativo)

@app.route('/dashboard')
@login_required
def dashboard():
    with sqlite3.connect(DB) as conn:
        # Total de ativos
        total_ativos = conn.execute("SELECT COUNT(*) FROM ativos").fetchone()[0]

        # Ativos por estado
        ativos_por_estado = conn.execute("""
            SELECT estado, COUNT(*) as count
            FROM ativos
            GROUP BY estado
        """).fetchall()

        # Ativos por localização (top 5)
        ativos_por_local = conn.execute("""
            SELECT localizacao, COUNT(*) as count
            FROM ativos
            GROUP BY localizacao
            ORDER BY count DESC
            LIMIT 5
        """).fetchall()

        # Últimos ativos adicionados
        ultimos_ativos = conn.execute("""
            SELECT * FROM ativos
            ORDER BY id DESC
            LIMIT 5
        """).fetchall()

    return render_template('dashboard.html',
                         total_ativos=total_ativos,
                         ativos_por_estado=ativos_por_estado,
                         ativos_por_local=ativos_por_local,
                         ultimos_ativos=ultimos_ativos)

@app.route('/relatorios')
@login_required
def relatorios():
    with sqlite3.connect(DB) as conn:
        # Buscar estados únicos
        estados = conn.execute("SELECT DISTINCT estado FROM ativos ORDER BY estado").fetchall()

        # Buscar localizações únicas
        localizacoes = conn.execute("SELECT DISTINCT localizacao FROM ativos ORDER BY localizacao").fetchall()

        # Buscar responsáveis únicos
        responsaveis = conn.execute("SELECT DISTINCT responsavel FROM ativos ORDER BY responsavel").fetchall()

    return render_template('relatorios.html',
                         estados=estados,
                         localizacoes=localizacoes,
                         responsaveis=responsaveis)

@app.route('/relatorio/estado/<estado>')
@login_required
def relatorio_estado(estado):
    try:
        with sqlite3.connect(DB) as conn:
            df = pd.read_sql_query("SELECT * FROM ativos WHERE estado = ?", conn, params=(estado,))

        if df.empty:
            flash(f'Não há ativos no estado "{estado}"!', 'warning')
            return redirect(url_for('relatorios'))

        file_path = f"relatorio_estado_{estado}.xlsx"
        df.to_excel(file_path, index=False)

        return send_file(file_path, as_attachment=True, download_name=f'relatorio_{estado}_{pd.Timestamp.now().strftime("%Y%m%d")}.xlsx')

    except Exception as e:
        flash(f'Erro ao gerar relatório: {str(e)}', 'error')
        return redirect(url_for('relatorios'))

@app.route('/relatorio/localizacao/<localizacao>')
@login_required
def relatorio_localizacao(localizacao):
    try:
        with sqlite3.connect(DB) as conn:
            df = pd.read_sql_query("SELECT * FROM ativos WHERE localizacao = ?", conn, params=(localizacao,))

        if df.empty:
            flash(f'Não há ativos na localização "{localizacao}"!', 'warning')
            return redirect(url_for('relatorios'))

        file_path = f"relatorio_localizacao.xlsx"
        df.to_excel(file_path, index=False)

        return send_file(file_path, as_attachment=True, download_name=f'relatorio_{localizacao.replace(" ", "_")}_{pd.Timestamp.now().strftime("%Y%m%d")}.xlsx')

    except Exception as e:
        flash(f'Erro ao gerar relatório: {str(e)}', 'error')
        return redirect(url_for('relatorios'))

@app.route('/relatorio/responsavel/<responsavel>')
@login_required
def relatorio_responsavel(responsavel):
    try:
        with sqlite3.connect(DB) as conn:
            df = pd.read_sql_query("SELECT * FROM ativos WHERE responsavel = ?", conn, params=(responsavel,))

        if df.empty:
            flash(f'Não há ativos sob responsabilidade de "{responsavel}"!', 'warning')
            return redirect(url_for('relatorios'))

        file_path = f"relatorio_responsavel.xlsx"
        df.to_excel(file_path, index=False)

        return send_file(file_path, as_attachment=True, download_name=f'relatorio_{responsavel.replace(" ", "_")}_{pd.Timestamp.now().strftime("%Y%m%d")}.xlsx')

    except Exception as e:
        flash(f'Erro ao gerar relatório: {str(e)}', 'error')
        return redirect(url_for('relatorios'))

@app.route('/relatorio/etiquetas')
@login_required
def relatorio_etiquetas():
    with sqlite3.connect(DB) as conn:
        ativos = conn.execute("SELECT * FROM ativos ORDER BY codigo_id").fetchall()

    return render_template('etiquetas.html', ativos=ativos)

@app.route('/admin/regenerar-qrcodes', methods=['POST'])
@login_required
def regenerar_qrcodes():
    """Regenera todos os QR codes com o URL atual"""
    try:
        with sqlite3.connect(DB) as conn:
            ativos = conn.execute("SELECT id FROM ativos").fetchall()

            if not ativos:
                flash('Nenhum ativo encontrado!', 'warning')
                return redirect(url_for('dashboard'))

            # Regenerar QR code para cada ativo
            for ativo in ativos:
                ativo_id = ativo[0]
                url = f"{BASE_URL}/ver/{ativo_id}"
                img = qrcode.make(url)
                img.save(f"{QR_FOLDER}/ativo_{ativo_id}.png")

            flash(f'{len(ativos)} QR codes regenerados com sucesso! Agora apontam para {BASE_URL}', 'success')

    except Exception as e:
        flash(f'Erro ao regenerar QR codes: {str(e)}', 'error')

    return redirect(url_for('dashboard'))

# ==================== ROTAS DE ANEXOS/FOTOS ====================

@app.route('/ativo/<int:ativo_id>/upload', methods=['POST'])
@login_required
def upload_anexo(ativo_id):
    """Upload de fotos e documentos"""
    try:
        if 'arquivo' not in request.files:
            flash('Nenhum arquivo selecionado!', 'error')
            return redirect(url_for('ativo', ativo_id=ativo_id))

        arquivo = request.files['arquivo']
        if arquivo.filename == '':
            flash('Nenhum arquivo selecionado!', 'error')
            return redirect(url_for('ativo', ativo_id=ativo_id))

        if arquivo and allowed_file(arquivo.filename):
            filename = secure_filename(arquivo.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{filename}"

            # Determinar tipo e pasta
            ext = filename.rsplit('.', 1)[1].lower()
            if ext in {'png', 'jpg', 'jpeg', 'gif'}:
                tipo = 'foto'
                pasta = 'fotos'
            else:
                tipo = 'documento'
                pasta = 'documentos'

            filepath = os.path.join(app.config['UPLOAD_FOLDER'], pasta, filename)
            arquivo.save(filepath)

            # Salvar no banco
            with sqlite3.connect(DB) as conn:
                conn.execute('''
                    INSERT INTO anexos (ativo_id, tipo, nome_arquivo, caminho, tamanho, mime_type, descricao, principal)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (ativo_id, tipo, arquivo.filename, filepath, os.path.getsize(filepath),
                      arquivo.content_type, request.form.get('descricao', ''), 0))
                conn.commit()

            registrar_historico(ativo_id, f'{tipo.capitalize()} adicionado', 'anexo', None, arquivo.filename)
            flash(f'{tipo.capitalize()} enviado com sucesso!', 'success')

        else:
            flash('Tipo de arquivo não permitido!', 'error')

    except Exception as e:
        flash(f'Erro ao fazer upload: {str(e)}', 'error')

    return redirect(url_for('ativo', ativo_id=ativo_id))

@app.route('/ativo/<int:ativo_id>/anexo/<int:anexo_id>/deletar', methods=['POST'])
@login_required
def deletar_anexo(ativo_id, anexo_id):
    """Deletar anexo"""
    try:
        with sqlite3.connect(DB) as conn:
            anexo = conn.execute('SELECT caminho, nome_arquivo FROM anexos WHERE id = ?', (anexo_id,)).fetchone()

            if anexo:
                # Deletar arquivo físico
                if os.path.exists(anexo[0]):
                    os.remove(anexo[0])

                # Deletar do banco
                conn.execute('DELETE FROM anexos WHERE id = ?', (anexo_id,))
                conn.commit()

                registrar_historico(ativo_id, 'Anexo removido', 'anexo', anexo[1], None)
                flash('Anexo removido com sucesso!', 'success')

    except Exception as e:
        flash(f'Erro ao remover anexo: {str(e)}', 'error')

    return redirect(url_for('ativo', ativo_id=ativo_id))

# ==================== ROTAS DE MANUTENÇÕES ====================

@app.route('/ativo/<int:ativo_id>/manutencao/adicionar', methods=['POST'])
@login_required
def adicionar_manutencao(ativo_id):
    """Adicionar registro de manutenção"""
    try:
        tipo = request.form['tipo']
        descricao = request.form['descricao']
        data_manutencao = request.form['data_manutencao']
        proximo_agendamento = request.form.get('proximo_agendamento') or None
        responsavel = request.form.get('responsavel', '')
        custo = request.form.get('custo') or None
        status = request.form.get('status', 'Concluída')
        observacoes = request.form.get('observacoes', '')

        with sqlite3.connect(DB) as conn:
            # Buscar nome do ativo para notificação
            ativo = conn.execute('SELECT nome FROM ativos WHERE id = ?', (ativo_id,)).fetchone()
            ativo_nome = ativo[0] if ativo else 'Ativo Desconhecido'

            conn.execute('''
                INSERT INTO manutencoes (ativo_id, tipo, descricao, data_manutencao,
                                       proximo_agendamento, responsavel, custo, status, observacoes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (ativo_id, tipo, descricao, data_manutencao, proximo_agendamento,
                  responsavel, custo, status, observacoes))
            conn.commit()

        registrar_historico(ativo_id, 'Manutenção registrada', 'manutenção', None, f'{tipo}: {descricao}')

        # Enviar notificação por email
        email_service.notificar_manutencao_adicionada({
            'ativo_id': ativo_id,
            'ativo_nome': ativo_nome,
            'tipo': tipo,
            'descricao': descricao,
            'data_manutencao': data_manutencao,
            'proximo_agendamento': proximo_agendamento,
            'responsavel': responsavel
        })

        flash('Manutenção registrada com sucesso!', 'success')

    except Exception as e:
        flash(f'Erro ao registrar manutenção: {str(e)}', 'error')

    return redirect(url_for('ativo', ativo_id=ativo_id))

@app.route('/manutencao/<int:manutencao_id>/deletar', methods=['POST'])
@login_required
def deletar_manutencao(manutencao_id):
    """Deletar registro de manutenção"""
    try:
        with sqlite3.connect(DB) as conn:
            manutencao = conn.execute('SELECT ativo_id FROM manutencoes WHERE id = ?', (manutencao_id,)).fetchone()

            if manutencao:
                conn.execute('DELETE FROM manutencoes WHERE id = ?', (manutencao_id,))
                conn.commit()

                registrar_historico(manutencao[0], 'Manutenção removida', 'manutenção', None, None)
                flash('Manutenção removida com sucesso!', 'success')
                return redirect(url_for('ativo', ativo_id=manutencao[0]))

    except Exception as e:
        flash(f'Erro ao remover manutenção: {str(e)}', 'error')

    return redirect(url_for('dashboard'))

# ==================== ROTAS DE CATEGORIAS ====================

@app.route('/categorias')
@login_required
def categorias():
    """Listar todas as categorias"""
    with sqlite3.connect(DB) as conn:
        # Buscar todas as categorias
        cats = conn.execute('''
            SELECT id, nome, descricao, icone, cor
            FROM categorias
            ORDER BY nome
        ''').fetchall()

        # Estatísticas por categoria
        stats = conn.execute('''
            SELECT c.nome, c.cor, c.icone, COUNT(a.id) as total
            FROM categorias c
            LEFT JOIN ativos a ON c.id = a.categoria_id
            GROUP BY c.id
            ORDER BY total DESC
        ''').fetchall()

        # Total de ativos
        total_ativos = conn.execute('SELECT COUNT(*) FROM ativos').fetchone()[0]

        # Ativos sem categoria
        sem_categoria = conn.execute('SELECT COUNT(*) FROM ativos WHERE categoria_id IS NULL').fetchone()[0]

    return render_template('categorias.html',
                         categorias=cats,
                         stats=stats,
                         total_ativos=total_ativos,
                         sem_categoria=sem_categoria)

@app.route('/categoria/<int:categoria_id>')
@login_required
def categoria(categoria_id):
    """Listar ativos de uma categoria"""
    with sqlite3.connect(DB) as conn:
        cat = conn.execute('SELECT id, nome, descricao, icone, cor FROM categorias WHERE id = ?', (categoria_id,)).fetchone()
        ativos_cat = conn.execute('SELECT * FROM ativos WHERE categoria_id = ? ORDER BY nome', (categoria_id,)).fetchall()

    if not cat:
        flash('Categoria não encontrada!', 'error')
        return redirect(url_for('categorias'))

    return render_template('categoria_ativos.html', categoria=cat, ativos=ativos_cat)

# ==================== ROTAS DE ALERTAS POR EMAIL ====================

@app.route('/alertas')
@login_required
def alertas():
    """Página de configuração de alertas por email"""
    # Obter configuração atual
    config = email_service.get_configuracao_email()

    # Estatísticas de alertas pendentes
    garantias_vencendo = email_service.verificar_garantias_vencendo(30)
    manutencoes_proximas = email_service.verificar_manutencoes_proximas(7)

    stats = {
        'garantias_vencendo': len(garantias_vencendo),
        'manutencoes_proximas': len(manutencoes_proximas)
    }

    return render_template('alertas.html', config=config, stats=stats)

@app.route('/alertas/teste', methods=['POST'])
@login_required
def enviar_email_teste():
    """Envia email de teste"""
    email_destino = request.form.get('email_teste')

    if not email_destino:
        flash('Por favor, informe um email de destino!', 'error')
        return redirect(url_for('alertas'))

    sucesso = email_service.enviar_email_teste(email_destino)

    if sucesso:
        flash(f'Email de teste enviado para {email_destino}!', 'success')
    else:
        flash('Erro ao enviar email de teste. Verifique as configurações SMTP.', 'error')

    return redirect(url_for('alertas'))

@app.route('/alertas/verificar-garantias', methods=['POST'])
@login_required
def verificar_garantias():
    """Verifica e envia alertas de garantias vencendo"""
    garantias = email_service.verificar_garantias_vencendo(30)

    if not garantias:
        flash('Nenhuma garantia vencendo nos próximos 30 dias.', 'info')
        return redirect(url_for('alertas'))

    sucesso = email_service.enviar_alerta_garantias()

    if sucesso:
        flash(f'Alerta de {len(garantias)} garantia(s) vencendo enviado com sucesso!', 'success')
    else:
        flash(f'Encontradas {len(garantias)} garantia(s) vencendo, mas não foi possível enviar o email.', 'warning')

    return redirect(url_for('alertas'))

@app.route('/alertas/verificar-manutencoes', methods=['POST'])
@login_required
def verificar_manutencoes():
    """Verifica e envia alertas de manutenções agendadas"""
    manutencoes = email_service.verificar_manutencoes_proximas(7)

    if not manutencoes:
        flash('Nenhuma manutenção agendada para os próximos 7 dias.', 'info')
        return redirect(url_for('alertas'))

    sucesso = email_service.enviar_alerta_manutencoes()

    if sucesso:
        flash(f'Lembrete de {len(manutencoes)} manutenção(ões) enviado com sucesso!', 'success')
    else:
        flash(f'Encontradas {len(manutencoes)} manutenção(ões) agendada(s), mas não foi possível enviar o email.', 'warning')

    return redirect(url_for('alertas'))

# ==================== INVENTÁRIOS ====================

@app.route('/inventarios')
@login_required
def inventarios():
    """Lista todos os inventários"""
    with sqlite3.connect(DB) as conn:
        inventarios_list = conn.execute('''
            SELECT i.*, c.nome as categoria_nome
            FROM inventarios i
            LEFT JOIN categorias c ON i.filtro_categoria_id = c.id
            ORDER BY i.data_inicio DESC
        ''').fetchall()

    return render_template('inventarios.html', inventarios=inventarios_list)

@app.route('/inventario/novo')
@login_required
def novo_inventario():
    """Formulário para criar novo inventário"""
    with sqlite3.connect(DB) as conn:
        categorias = conn.execute('SELECT id, nome FROM categorias ORDER BY nome').fetchall()
        localizacoes = conn.execute('SELECT DISTINCT localizacao FROM ativos WHERE localizacao IS NOT NULL ORDER BY localizacao').fetchall()
        responsaveis = conn.execute('SELECT DISTINCT responsavel FROM ativos WHERE responsavel IS NOT NULL ORDER BY responsavel').fetchall()

    return render_template('novo_inventario.html', categorias=categorias, localizacoes=localizacoes, responsaveis=responsaveis)

@app.route('/inventario/criar', methods=['POST'])
@login_required
def criar_inventario():
    """Cria um novo inventário"""
    try:
        titulo = request.form['titulo']
        descricao = request.form.get('descricao', '')
        tipo = request.form['tipo']  # 'completo', 'categoria', 'localizacao', 'responsavel'

        filtro_categoria = request.form.get('filtro_categoria')
        filtro_localizacao = request.form.get('filtro_localizacao')
        filtro_responsavel = request.form.get('filtro_responsavel')

        with sqlite3.connect(DB) as conn:
            # Criar inventário
            cursor = conn.execute('''
                INSERT INTO inventarios (titulo, descricao, tipo, filtro_categoria_id, filtro_localizacao, filtro_responsavel)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (titulo, descricao, tipo, filtro_categoria, filtro_localizacao, filtro_responsavel))

            inventario_id = cursor.lastrowid

            # Buscar ativos conforme filtro
            query = "SELECT id FROM ativos WHERE 1=1"
            params = []

            if tipo == 'categoria' and filtro_categoria:
                query += " AND categoria_id = ?"
                params.append(filtro_categoria)
            elif tipo == 'localizacao' and filtro_localizacao:
                query += " AND localizacao = ?"
                params.append(filtro_localizacao)
            elif tipo == 'responsavel' and filtro_responsavel:
                query += " AND responsavel = ?"
                params.append(filtro_responsavel)

            ativos = conn.execute(query, params).fetchall()

            # Adicionar ativos ao inventário
            for ativo in ativos:
                conn.execute('''
                    INSERT INTO inventario_itens (inventario_id, ativo_id, status)
                    VALUES (?, ?, 'Pendente')
                ''', (inventario_id, ativo[0]))

            # Atualizar total de ativos
            conn.execute('''
                UPDATE inventarios SET total_ativos = ? WHERE id = ?
            ''', (len(ativos), inventario_id))

            conn.commit()

        flash(f'Inventário "{titulo}" criado com sucesso! {len(ativos)} ativos incluídos.', 'success')
        return redirect(url_for('executar_inventario', inventario_id=inventario_id))

    except Exception as e:
        flash(f'Erro ao criar inventário: {str(e)}', 'error')
        return redirect(url_for('novo_inventario'))

@app.route('/inventario/<int:inventario_id>')
@login_required
def executar_inventario(inventario_id):
    """Executa o inventário (checklist)"""
    with sqlite3.connect(DB) as conn:
        # Dados do inventário
        inventario = conn.execute('SELECT * FROM inventarios WHERE id = ?', (inventario_id,)).fetchone()

        if not inventario:
            flash('Inventário não encontrado.', 'error')
            return redirect(url_for('inventarios'))

        # Itens do inventário com dados dos ativos
        itens = conn.execute('''
            SELECT
                ii.id, ii.status, ii.observacao, ii.conferido_por, ii.data_conferencia,
                a.id as ativo_id, a.codigo_id, a.nome, a.sn, a.localizacao, a.responsavel, a.estado,
                c.nome as categoria_nome, c.icone as categoria_icone
            FROM inventario_itens ii
            JOIN ativos a ON ii.ativo_id = a.id
            LEFT JOIN categorias c ON a.categoria_id = c.id
            WHERE ii.inventario_id = ?
            ORDER BY ii.status, a.codigo_id
        ''', (inventario_id,)).fetchall()

    return render_template('executar_inventario.html', inventario=inventario, itens=itens)

@app.route('/inventario/<int:inventario_id>/conferir/<int:ativo_id>', methods=['POST'])
@login_required
def conferir_item_inventario(inventario_id, ativo_id):
    """Marca um item como conferido ou não localizado"""
    try:
        novo_status = request.form.get('status', 'Conferido')  # 'Conferido' ou 'Não Localizado'
        observacao = request.form.get('observacao', '')

        with sqlite3.connect(DB) as conn:
            # Atualizar item
            conn.execute('''
                UPDATE inventario_itens
                SET status = ?, observacao = ?, conferido_por = 'Admin', data_conferencia = CURRENT_TIMESTAMP
                WHERE inventario_id = ? AND ativo_id = ?
            ''', (novo_status, observacao, inventario_id, ativo_id))

            # Recalcular totais
            totais = conn.execute('''
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'Conferido' THEN 1 ELSE 0 END) as conferidos,
                    SUM(CASE WHEN status = 'Não Localizado' THEN 1 ELSE 0 END) as nao_localizados
                FROM inventario_itens
                WHERE inventario_id = ?
            ''', (inventario_id,)).fetchone()

            # Atualizar inventário
            conn.execute('''
                UPDATE inventarios
                SET total_conferidos = ?, total_nao_localizados = ?
                WHERE id = ?
            ''', (totais[1], totais[2], inventario_id))

            conn.commit()

        return jsonify({'success': True, 'status': novo_status})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/inventario/<int:inventario_id>/finalizar', methods=['POST'])
@login_required
def finalizar_inventario(inventario_id):
    """Finaliza o inventário"""
    try:
        with sqlite3.connect(DB) as conn:
            conn.execute('''
                UPDATE inventarios
                SET status = 'Concluído', data_conclusao = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (inventario_id,))
            conn.commit()

        flash('Inventário finalizado com sucesso!', 'success')
        return redirect(url_for('relatorio_inventario', inventario_id=inventario_id))

    except Exception as e:
        flash(f'Erro ao finalizar inventário: {str(e)}', 'error')
        return redirect(url_for('executar_inventario', inventario_id=inventario_id))

@app.route('/inventario/<int:inventario_id>/relatorio')
@login_required
def relatorio_inventario(inventario_id):
    """Relatório de divergências do inventário"""
    with sqlite3.connect(DB) as conn:
        # Dados do inventário
        inventario = conn.execute('SELECT * FROM inventarios WHERE id = ?', (inventario_id,)).fetchone()

        if not inventario:
            flash('Inventário não encontrado.', 'error')
            return redirect(url_for('inventarios'))

        # Itens conferidos
        conferidos = conn.execute('''
            SELECT
                a.codigo_id, a.nome, a.localizacao, ii.conferido_por, ii.data_conferencia
            FROM inventario_itens ii
            JOIN ativos a ON ii.ativo_id = a.id
            WHERE ii.inventario_id = ? AND ii.status = 'Conferido'
            ORDER BY a.codigo_id
        ''', (inventario_id,)).fetchall()

        # Itens não localizados
        nao_localizados = conn.execute('''
            SELECT
                a.codigo_id, a.nome, a.localizacao, a.responsavel, ii.observacao
            FROM inventario_itens ii
            JOIN ativos a ON ii.ativo_id = a.id
            WHERE ii.inventario_id = ? AND ii.status = 'Não Localizado'
            ORDER BY a.codigo_id
        ''', (inventario_id,)).fetchall()

        # Itens pendentes
        pendentes = conn.execute('''
            SELECT
                a.codigo_id, a.nome, a.localizacao, a.responsavel
            FROM inventario_itens ii
            JOIN ativos a ON ii.ativo_id = a.id
            WHERE ii.inventario_id = ? AND ii.status = 'Pendente'
            ORDER BY a.codigo_id
        ''', (inventario_id,)).fetchall()

    return render_template('relatorio_inventario.html',
                         inventario=inventario,
                         conferidos=conferidos,
                         nao_localizados=nao_localizados,
                         pendentes=pendentes)

@app.route('/inventario/<int:inventario_id>/exportar')
@login_required
def exportar_inventario(inventario_id):
    """Exporta o inventário para Excel"""
    try:
        with sqlite3.connect(DB) as conn:
            # Dados do inventário
            inventario = conn.execute('SELECT * FROM inventarios WHERE id = ?', (inventario_id,)).fetchone()

            if not inventario:
                flash('Inventário não encontrado.', 'error')
                return redirect(url_for('inventarios'))

            # Todos os itens
            itens = conn.execute('''
                SELECT
                    a.codigo_id as 'Código',
                    a.nome as 'Nome',
                    a.sn as 'SN',
                    a.localizacao as 'Localização',
                    a.responsavel as 'Responsável',
                    c.nome as 'Categoria',
                    ii.status as 'Status',
                    ii.conferido_por as 'Conferido Por',
                    ii.data_conferencia as 'Data Conferência',
                    ii.observacao as 'Observação'
                FROM inventario_itens ii
                JOIN ativos a ON ii.ativo_id = a.id
                LEFT JOIN categorias c ON a.categoria_id = c.id
                WHERE ii.inventario_id = ?
                ORDER BY ii.status, a.codigo_id
            ''', (inventario_id,)).fetchall()

        # Criar DataFrame
        df = pd.DataFrame(itens, columns=['Código', 'Nome', 'SN', 'Localização', 'Responsável',
                                         'Categoria', 'Status', 'Conferido Por', 'Data Conferência', 'Observação'])

        # Salvar em Excel
        filename = f"inventario_{inventario_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        filepath = os.path.join('static', 'exports', filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # Aba principal
            df.to_excel(writer, sheet_name='Inventário Completo', index=False)

            # Aba de resumo
            resumo_data = {
                'Métrica': ['Total de Ativos', 'Conferidos', 'Não Localizados', 'Pendentes',
                           '% Conferidos', '% Não Localizados'],
                'Valor': [
                    inventario[8],  # total_ativos
                    inventario[9],  # total_conferidos
                    inventario[10], # total_nao_localizados
                    inventario[8] - inventario[9] - inventario[10],  # pendentes
                    f"{(inventario[9]/inventario[8]*100):.1f}%" if inventario[8] > 0 else "0%",
                    f"{(inventario[10]/inventario[8]*100):.1f}%" if inventario[8] > 0 else "0%"
                ]
            }
            df_resumo = pd.DataFrame(resumo_data)
            df_resumo.to_excel(writer, sheet_name='Resumo', index=False)

        return send_file(filepath, as_attachment=True, download_name=filename)

    except Exception as e:
        flash(f'Erro ao exportar inventário: {str(e)}', 'error')
        return redirect(url_for('relatorio_inventario', inventario_id=inventario_id))

# ==================== AUTENTICAÇÃO E USUÁRIOS ====================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember', False)

        if not username or not password:
            flash('Por favor, preencha usuário e senha', 'error')
            return render_template('login.html')

        try:
            with sqlite3.connect(DB) as conn:
                user_data = conn.execute(
                    'SELECT id, username, email, nome, perfil, ativo, senha_hash FROM usuarios WHERE username = ?',
                    (username,)
                ).fetchone()

                if user_data and check_password_hash(user_data[6], password):
                    if not user_data[5]:  # ativo
                        flash('Usuário desativado. Contate o administrador.', 'error')
                        app.logger.warning(f'Tentativa de login com usuário desativado: {username}')
                        return render_template('login.html')

                    user = User(user_data[0], user_data[1], user_data[2], user_data[3], user_data[4], user_data[5])
                    login_user(user, remember=remember)

                    # Atualizar último acesso
                    conn.execute('UPDATE usuarios SET ultimo_acesso = CURRENT_TIMESTAMP WHERE id = ?', (user.id,))
                    conn.commit()

                    app.logger.info(f'Login bem-sucedido: {username}')
                    flash(f'Bem-vindo, {user.nome}!', 'success')

                    next_page = request.args.get('next')
                    return redirect(next_page if next_page else url_for('dashboard'))
                else:
                    flash('Usuário ou senha incorretos', 'error')
                    app.logger.warning(f'Tentativa de login falhou: {username}')

        except Exception as e:
            flash('Erro ao fazer login. Tente novamente.', 'error')
            app.logger.error(f'Erro no login: {e}')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """Logout do usuário"""
    app.logger.info(f'Logout: {current_user.username}')
    logout_user()
    flash('Você saiu do sistema.', 'info')
    return redirect(url_for('login'))

@app.route('/usuarios')
@login_required
def usuarios():
    """Lista todos os usuários (apenas admin)"""
    if not current_user.is_admin():
        flash('Acesso negado. Apenas administradores.', 'error')
        return redirect(url_for('dashboard'))

    with sqlite3.connect(DB) as conn:
        usuarios_list = conn.execute('''
            SELECT id, username, email, nome, perfil, ativo, ultimo_acesso, criado_em
            FROM usuarios
            ORDER BY criado_em DESC
        ''').fetchall()

    return render_template('usuarios.html', usuarios=usuarios_list)

@app.route('/usuario/novo', methods=['GET', 'POST'])
@login_required
def novo_usuario():
    """Criar novo usuário (apenas admin)"""
    if not current_user.is_admin():
        flash('Acesso negado. Apenas administradores.', 'error')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        try:
            username = request.form['username']
            email = request.form['email']
            nome = request.form['nome']
            perfil = request.form['perfil']
            senha = request.form['senha']
            senha_confirmacao = request.form['senha_confirmacao']

            if senha != senha_confirmacao:
                flash('As senhas não coincidem', 'error')
                return render_template('novo_usuario.html')

            if len(senha) < 6:
                flash('A senha deve ter pelo menos 6 caracteres', 'error')
                return render_template('novo_usuario.html')

            senha_hash = generate_password_hash(senha)

            with sqlite3.connect(DB) as conn:
                conn.execute('''
                    INSERT INTO usuarios (username, email, senha_hash, nome, perfil, ativo)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (username, email, senha_hash, nome, perfil, True))
                conn.commit()

            app.logger.info(f'Novo usuário criado: {username} por {current_user.username}')
            flash(f'Usuário {username} criado com sucesso!', 'success')
            return redirect(url_for('usuarios'))

        except sqlite3.IntegrityError:
            flash('Usuário ou e-mail já existe', 'error')
        except Exception as e:
            flash(f'Erro ao criar usuário: {str(e)}', 'error')
            app.logger.error(f'Erro ao criar usuário: {e}')

    return render_template('novo_usuario.html')

@app.route('/usuario/<int:user_id>/toggle', methods=['POST'])
@login_required
def toggle_usuario(user_id):
    """Ativar/desativar usuário (apenas admin)"""
    if not current_user.is_admin():
        flash('Acesso negado', 'error')
        return redirect(url_for('dashboard'))

    if user_id == current_user.id:
        flash('Você não pode desativar sua própria conta', 'error')
        return redirect(url_for('usuarios'))

    try:
        with sqlite3.connect(DB) as conn:
            user = conn.execute('SELECT username, ativo FROM usuarios WHERE id = ?', (user_id,)).fetchone()

            if user:
                novo_status = not user[1]
                conn.execute('UPDATE usuarios SET ativo = ? WHERE id = ?', (novo_status, user_id))
                conn.commit()

                status_texto = 'ativado' if novo_status else 'desativado'
                app.logger.info(f'Usuário {user[0]} {status_texto} por {current_user.username}')
                flash(f'Usuário {user[0]} {status_texto}', 'success')

    except Exception as e:
        flash('Erro ao alterar status do usuário', 'error')
        app.logger.error(f'Erro ao toggle usuário: {e}')

    return redirect(url_for('usuarios'))

@app.route('/perfil', methods=['GET', 'POST'])
@login_required
def perfil():
    """Perfil do usuário - trocar senha"""
    if request.method == 'POST':
        try:
            senha_atual = request.form['senha_atual']
            nova_senha = request.form['nova_senha']
            confirmar_senha = request.form['confirmar_senha']

            if nova_senha != confirmar_senha:
                flash('As novas senhas não coincidem', 'error')
                return render_template('perfil.html')

            if len(nova_senha) < 6:
                flash('A senha deve ter pelo menos 6 caracteres', 'error')
                return render_template('perfil.html')

            with sqlite3.connect(DB) as conn:
                user = conn.execute('SELECT senha_hash FROM usuarios WHERE id = ?', (current_user.id,)).fetchone()

                if user and check_password_hash(user[0], senha_atual):
                    novo_hash = generate_password_hash(nova_senha)
                    conn.execute('UPDATE usuarios SET senha_hash = ? WHERE id = ?', (novo_hash, current_user.id))
                    conn.commit()

                    app.logger.info(f'Senha alterada: {current_user.username}')
                    flash('Senha alterada com sucesso!', 'success')
                    return redirect(url_for('dashboard'))
                else:
                    flash('Senha atual incorreta', 'error')

        except Exception as e:
            flash('Erro ao alterar senha', 'error')
            app.logger.error(f'Erro ao alterar senha: {e}')

    return render_template('perfil.html')

# Error Handlers
@app.errorhandler(404)
def not_found_error(error):
    app.logger.warning(f'Página não encontrada: {request.url}')
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f'Erro interno: {error}')
    return render_template('500.html'), 500

@app.errorhandler(403)
def forbidden_error(error):
    app.logger.warning(f'Acesso negado: {request.url}')
    return render_template('403.html'), 403

# ==================== SCHEDULER DE ALERTAS AUTOMÁTICOS ====================

# Configurar scheduler para verificações automáticas
scheduler = BackgroundScheduler()

# Executar verificação de alertas diariamente às 9h
scheduler.add_job(
    func=email_service.executar_verificacao_alertas,
    trigger="cron",
    hour=9,
    minute=0,
    id='verificacao_alertas_diaria'
)

# Iniciar scheduler
scheduler.start()

# Desligar scheduler quando app terminar
atexit.register(lambda: scheduler.shutdown())

print("\n✅ Scheduler de alertas automáticos iniciado")
print("   → Verificações diárias às 9h00")
print("   → Alertas de garantias (30 dias)")
print("   → Alertas de manutenções (7 dias)\n")

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
