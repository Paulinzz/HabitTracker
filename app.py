from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user, LoginManager, UserMixin, login_user, logout_user
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///habits.db'
app.config["SECRET_KEY"] = "secreto_muito_seguro_e_longo_por_favor_mude_isso_em_producao" 

db = SQLAlchemy(app)

class Habito(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    senha = db.Column(db.String(100), nullable=False) 
    usuario = db.Column(db.String(100), nullable=False, unique=True) 
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.String(200), nullable=False)

    def get_id(self):
        return str(self.id)

    def __repr__(self):
        return f"<Habito {self.usuario}>"

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' 

@login_manager.user_loader
def load_user(user_id):
    return Habito.query.get(int(user_id))

with app.app_context():
    db.create_all()  

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('habitos'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('habitos'))

    if request.method == 'POST':
        usuario = request.form['usuario']
        senha = request.form['senha']
        user = Habito.query.filter_by(usuario=usuario).first()

        if user and user.senha == senha: 
            login_user(user) 
            flash('Login realizado com sucesso!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('habitos'))
        else:
            flash('Usuário ou senha inválidos.', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('habitos'))

    if request.method == 'POST':
        usuario = request.form['usuario']
        senha = request.form['senha']
        nome = request.form.get('nome', 'Novo Hábito') 
        descricao = request.form.get('descricao', 'Hábito criado no cadastro.') 

        existing_user = Habito.query.filter_by(usuario=usuario).first()
        if existing_user:
            flash('Nome de usuário já existe. Por favor, escolha outro.', 'danger')
            return redirect(url_for('register'))


        novo_habito = Habito(usuario=usuario, senha=senha, nome=nome, descricao=descricao)
        db.session.add(novo_habito)
        db.session.commit()
        flash('Usuário registrado com sucesso! Por favor, faça login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você foi desconectado.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required 
def habitos():

    user_habitos = Habito.query.filter_by(id=current_user.id).all()
    return render_template('dashboard.html', habitos=user_habitos)

# Example route to add a new habit for the current user
@app.route('/add_habit', methods=['GET', 'POST'])
@login_required
def add_habit():
    if request.method == 'POST':
        nome = request.form['nome']
        descricao = request.form['descricao']

        current_user.nome = nome
        current_user.descricao = descricao
        db.session.commit()
        flash('Hábito atualizado com sucesso!', 'success')
        return redirect(url_for('habitos'))
    return render_template('add_habit.html') # You'll need to create this template

if __name__ == '__main__':
    app.run(debug=True)