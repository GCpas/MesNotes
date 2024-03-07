from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from sqlalchemy import func
from flask_restful import Api, Resource
import requests

app = Flask(__name__)

# Initialisation de l'application Flask
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///MesNotes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key_here'

# Initialisation de l'extension SQLAlchemy et de l'API
db = SQLAlchemy(app)
api = Api(app)

# Définition du modèle Connexion pour la table 'connexion'
class Connexion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_meteo = db.Column(db.Integer, db.ForeignKey('meteo.id'), nullable=True)
    nom = db.Column(db.String(255), nullable=False)
    mdp = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return '<Connexion %r>' % self.nom
    
class Meteo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    api = db.Column(db.String(255), nullable=False)
    geoapi = db.Column(db.String(255), nullable=False)
    nom = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return '<Meteo %r>' % self.id

class Notes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_connexion = db.Column(db.Integer, db.ForeignKey('connexion.id'), nullable=True)
    titre = db.Column(db.String(255), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __rep__(self):
        return f'<Note {self.id}: {self.titre}>'

#RESTful
#météo
class MeteoUtilisateur(Resource):
    def get(self, nom_utilisateur):
        utilisateur = Connexion.query.filter_by(nom=nom_utilisateur).first()
        if not utilisateur:
            return {"message": "Utilisateur non trouvé"}, 404

        meteo = Meteo.query.get(utilisateur.id_meteo)
        if not meteo:
            return {"message": "Information météo non disponible"}, 404

        url = f'{meteo.geoapi}appid={meteo.api}&units=metric'
        response = requests.get(url)
        weather_data = response.json()

        return {"nom_utilisateur": nom_utilisateur, "ville": meteo.nom, "weather_data": weather_data}, 200

api.add_resource(MeteoUtilisateur, '/utilisateur/<string:nom_utilisateur>/weather')

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

    utilisateur = Connexion.query.filter_by(nom=nom).first()
    if not utilisateur:
        return "Utilisateur non trouvé"

    meteo = Meteo.query.get(utilisateur.id_meteo)
    if not meteo:
        return "Information météo non disponible"

    url = f'{meteo.geoapi}appid={meteo.api}&units=metric'
    response = requests.get(url)
    weather_data = response.json()

    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search_query', '')

    # Filtrage par titre
    notes_query = Notes.query.filter(Notes.id_connexion == utilisateur.id)
    if search_query:
        notes_query = notes_query.filter(Notes.titre.ilike(f"%{search_query}%"))

    # Tri des notes
    sort_order = request.args.get('sort_order', 'desc')
    if sort_order == 'desc':
        notes_query = notes_query.order_by(Notes.date.desc())
    else:
        notes_query = notes_query.order_by(Notes.date.asc())

    # Récupération des notes paginées
    notes = notes_query.paginate(page=page, per_page=4)

    return render_template('utilisateur.html', nom_utilisateur=nom, weather_data=weather_data, ville=meteo.nom, notes=notes)

def verifier_identifiants(nom_utilisateur, mot_de_passe):
    utilisateur = Connexion.query.filter_by(nom=nom_utilisateur, mdp=mot_de_passe).first()
    return utilisateur is not None

# Route pour la création de note
@app.route('/utilisateur/<nom>/creer-note', methods=['GET', 'POST'])
def creer_note(nom):
    if request.method == 'POST':
        titre = request.form['titre']
        message = request.form['message']

        # Récupérer l'utilisateur
        utilisateur = Connexion.query.filter_by(nom=nom).first()

        # Créer une nouvelle note
        nouvelle_note = Notes(titre=titre, message=message, id_connexion=utilisateur.id)

        try:
            # Ajouter la note à la base de données
            db.session.add(nouvelle_note)
            db.session.commit()
            return redirect(url_for('utilisateur', nom=nom))
        except:
            return 'Une erreur s\'est produite lors de la création de la note'

    else:
        return render_template('creer_note.html', nom_utilisateur=nom)

@app.route('/utilisateur/<nom>/modifiernote', methods=['GET', 'POST'])
def modifier_note(nom):
    if request.method == 'POST':
        titre = request.form.get('titre')
        ancien_message = request.form.get('ancien_message')
        nouveau_message = request.form.get('message')

        # Recherche de l'utilisateur dans la base de données
        utilisateur = Connexion.query.filter_by(nom=nom).first()
        if utilisateur:
            # Recherche de la note correspondante
            note = Notes.query.filter_by(titre=titre, message=ancien_message, id_connexion=utilisateur.id).first()
            if note:
                # Met à jour le message de la note
                note.message = nouveau_message
                db.session.commit()
                return redirect(url_for('utilisateur', nom=nom))
            else:
                return "Note non trouvée"
        else:
            return "Utilisateur non trouvé"
    else:
        return render_template('modifier_note.html')
    
@app.route('/utilisateur/<nom>/supprimer-note', methods=['GET', 'POST'])
def supprimer_note(nom):
    if request.method == 'POST':
        titre = request.form.get('titre')

        # Recherche de l'utilisateur dans la base de données
        utilisateur = Connexion.query.filter_by(nom=nom).first()
        if utilisateur:
            # Recherche de la note correspondante par le titre
            note = Notes.query.filter_by(titre=titre, id_connexion=utilisateur.id).first()
            if note:
                # Supprime la note de la base de données
                db.session.delete(note)
                db.session.commit()
                return redirect(url_for('utilisateur', nom=nom))
            else:
                return "Note non trouvée"
        else:
            return "Utilisateur non trouvé"
    else:
        return render_template('supprimer_note.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)