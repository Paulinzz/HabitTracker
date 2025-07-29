from flask import Flask, render_template, request, redirect, url_for, flash 
from flask_sqlalchemy import SQLAlchemy 

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///habits.db'
app.config["SECRET_KEY"] = "secreto"

db = SQLAlchemy(app)

class Habito(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)

with app.app_context():
    db.create_all()  # Cria o banco de dados e as tabelas

@app.route('/')
def index():
    habitos = Habito.query.all()
    return render_template('index.html', habitos=habitos)

@app.route('/add', methods=['POST'])
def add_habito():
    nome = request.form['nome']
    novo_habito = Habito(nome=nome)
    db.session.add(novo_habito)
    db.session.commit()
    flash('Hábito adicionado com sucesso!', 'success')
    return redirect(url_for('index'))

@app.route('/delete/<int:id>')
def delete_habito(id):
    habito = Habito.query.get_or_404(id)
    db.session.delete(habito)
    db.session.commit()
    flash('Hábito deletado com sucesso!', 'success')
    return redirect(url_for('index'))

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_habito(id):
    habito = Habito.query.get_or_404(id)
    if request.method == 'POST':
        habito.nome = request.form['nome']
        db.session.commit()
        flash('Hábito atualizado com sucesso!', 'success')
        return redirect(url_for('index'))
    return render_template('edit.html', habito=habito)

@app.route('/search', methods=['GET'])
def search_habito():
    query = request.args.get('query')
    if query:
        habitos = Habito.query.filter(Habito.nome.contains(query)).all()
    else:
        habitos = Habito.query.all()
    return render_template('index.html', habitos=habitos)

if __name__ == '__main__':
    app.run(debug=True)
