from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Initialisation de l'application Flask
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///MesNotes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key_here'

# Initialisation de l'extension SQLAlchemy
db = SQLAlchemy(app)

# Définition du modèle Connexion pour la table 'connexion'
class Connexion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(255), nullable=False)
    mdp = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return '<Connexion %r>' % self.nom

# Route pour la page de connexion
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        nom_utilisateur = request.form.get('nom')
        mot_de_passe = request.form.get('mdp')

        if verifier_identifiants(nom_utilisateur, mot_de_passe):
            return redirect(url_for('utilisateur', nom=nom_utilisateur))
        else:
            return "Identifiant faux"
    
    else:
        return render_template('index.html')

# Route pour la page utilisateur
@app.route('/utilisateur/<nom>')
def utilisateur(nom):
    return render_template('utilisateur.html', nom_utilisateur=nom)

def verifier_identifiants(nom_utilisateur, mot_de_passe):
    utilisateur = Connexion.query.filter_by(nom=nom_utilisateur, mdp=mot_de_passe).first()
    return utilisateur is not None

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)