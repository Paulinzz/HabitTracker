from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user, LoginManager, UserMixin, login_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///habits.db'
app.config["SECRET_KEY"] = "secreto_muito_seguro_e_longo_por_favor_mude_isso_em_producao" 

db = SQLAlchemy(app)

# Modelo de Usuário: APENAS esta classe deve herdar de UserMixin e lidar com autenticação
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    password_hash = db.Column(db.String(150), nullable=False) # Armazenar o hash da senha

    # Relação com os hábitos: um usuário pode ter muitos hábitos
    # 'Habit' é o nome da classe do modelo Hábito
    # 'backref='owner'' cria um atributo 'owner' no objeto Habit para acessar o User
    habits = db.relationship('Habit', backref='owner', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password) # Usa o password_hash para a verificação
    
    def get_id(self):
        return str(self.id)
    
    def __repr__(self):
        return f"<User {self.username}>"

# Modelo de Hábito: APENAS esta classe deve lidar com os detalhes dos hábitos
class Habit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200), nullable=True) # Descrição pode ser opcional
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # Chave estrangeira para o usuário

    def __repr__(self):
        return f"<Habit {self.name} for User ID: {self.user_id}>"

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' 

@login_manager.user_loader
def load_user(user_id):
    # O user_loader DEVE carregar o objeto User
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()  

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard')) # Redireciona para o dashboard se logado
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['usuario'] 
        password = request.form['senha']   
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password): # Chama o método check_password do modelo User
            login_user(user) 
            flash('Login realizado com sucesso!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Usuário ou senha inválidos.', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['usuario']
        password = request.form['senha']
        
        existing_user = User.query.filter_by(username=username).first() # Verifica se o username já existe no modelo User
        if existing_user:
            flash('Nome de usuário já existe. Por favor, escolha outro.', 'danger')
            return redirect(url_for('register'))

        new_user = User(username=username)
        new_user.set_password(password) # Hash da senha usando o método do modelo User
        
        db.session.add(new_user)
        db.session.commit()
        flash('Usuário registrado com sucesso! Por favor, faça login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

# Rota para o Dashboard que lista os hábitos do usuário
@app.route('/dashboard')
@login_required 
def dashboard(): # Nome da função agora é 'dashboard'
    # current_user agora é um objeto User, e current_user.habits acessa os hábitos relacionados a ele
    user_habits = current_user.habits 
    return render_template('dashboard.html', habits=user_habits)

# Rota para adicionar um novo hábito (via POST do formulário no modal)
@app.route('/add_habit', methods=['POST', 'GET']) # Método deve ser POST para submissão de formulário
@login_required
def add_habit():
    if request.method == 'POST':
        # Assegure-se que os nomes dos campos (name, description) batem com seu formulário HTML
        name = request.form.get('habit_name')      
        description = request.form.get('description') 

        if not name:
            flash('O nome do hábito é obrigatório!', 'danger')
            return redirect(url_for('dashboard')) # Redireciona de volta para o dashboard se o nome não for fornecido

        # Cria uma nova instância de Habit e a associa ao usuário logado (current_user)
        new_habit = Habit(name=name, description=description, owner=current_user) 
        db.session.add(new_habit)
        db.session.commit()
        flash(f'Hábito "{name}" adicionado com sucesso!', 'success')
        return redirect(url_for('dashboard')) # Redireciona para o dashboard após adicionar

@app.route('/delete_habit', methods=['POST'])
@login_required
def delete_habit():
    habit_id = request.form.get('habit_id') # Pega o ID do hábito do formulário

    if not habit_id:
        flash('Nenhum hábito foi selecionado para exclusão.', 'danger')
        return redirect(url_for('dashboard'))

    try:
        # Tenta encontrar o hábito pelo ID e garantir que pertence ao usuário logado
        habit_to_delete = Habit.query.filter_by(id=habit_id, user_id=current_user.id).first()

        if habit_to_delete:
            db.session.delete(habit_to_delete) # Marca o hábito para exclusão
            db.session.commit() # Confirma a exclusão no banco de dados
            flash(f'Hábito "{habit_to_delete.name}" excluído com sucesso!', 'success')
        else:
            flash('Hábito não encontrado ou você não tem permissão para excluí-lo.', 'danger')
    except Exception as e:
        db.session.rollback() # Em caso de erro, desfaz a operação
        flash(f'Ocorreu um erro ao excluir o hábito: {e}', 'danger')
    
    return redirect(url_for('dashboard'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você foi desconectado.', 'info')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)