#Importation des modules suivant :
from flask import Flask, render_template, request, redirect, url_for #Flask ainsi que c'est fonctionnalité
from flask_sqlalchemy import SQLAlchemy #SQLAlchemy pour lire et écrire dans une BDD
from datetime import datetime, timedelta #datetime pour la gestion de la date et de l'heure
from sqlalchemy import func #des fonctionnalité spécifiques de SQLAlchemy
from flask_restful import Api, Resource #Flask-RESTful ainsi que c'est fonctionnalité
import requests #requests pour les requêtes HTTP

#Initialisation de l'extension Flask
app = Flask(__name__)

# Configuration de la BDD (le chemin mis veux dire qu'il est a la racine du projet) SQLAlchemy et définition secrète de la clé secrète pour Flask
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///MesNotes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key_here'

# Initialisation de l'extension SQLAlchemy et de l'API (RESTful)
db = SQLAlchemy(app)
api = Api(app)

# Définition des modèles de données de chaque table de la BDD "MesNotes.db"
# table "connexion" (structuration)
class Connexion(db.Model):
        #définition des colonnes
    id = db.Column(db.Integer, primary_key=True)
    id_meteo = db.Column(db.Integer, db.ForeignKey('meteo.id'), nullable=True)
    nom = db.Column(db.String(255), nullable=False)
    mdp = db.Column(db.String(255), nullable=False)

    #sert a retourner une chaîne de caractères représentant l'objet Connexion.
    def __repr__(self):
        return '<Connexion %r>' % self.nom

# table "meteo" (structuration)    
class Meteo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    api = db.Column(db.String(255), nullable=False)
    geoapi = db.Column(db.String(255), nullable=False)
    nom = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return '<Meteo %r>' % self.id

# table "notes" (structuration)  
class Notes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_connexion = db.Column(db.Integer, db.ForeignKey('connexion.id'), nullable=True)
    titre = db.Column(db.String(255), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __rep__(self):
        return f'<Note {self.id}: {self.titre}>'

#Utilisation de RESTful pour la météo
class MeteoUtilisateur(Resource):
    def get(self, nom_utilisateur):
        #Récupération de l'utilisateur à partir de la BDD
        utilisateur = Connexion.query.filter_by(nom=nom_utilisateur).first()
        #Si pas d'utilisateur, alors il retourne que l'utilisateur n'a pas était trouvé
        if not utilisateur:
            return {"message": "Utilisateur non trouvé"}, 404

        #Récupération des données météologiques (toujours dans la BDD, table meteo) qui est associé a l'utilisateur
        meteo = Meteo.query.get(utilisateur.id_meteo)
        #Si il ne trouve rien, alors il retourne une erreur
        if not meteo:
            return {"message": "Information météo non disponible"}, 404

        #Récupération des données météologiques à partir de l'API (création du lien avec ce qui est dans la table meteo)
        url = f'{meteo.geoapi}appid={meteo.api}&units=metric'
        #Envoi une requête GET à l'URL de l'API météo pour récupérer les données
        response = requests.get(url)
        #Conversion des données en JSON
        weather_data = response.json()

        #retourne les données métérologique (nom de l'utilisateur, ville et les données).
        return {"nom_utilisateur": nom_utilisateur, "ville": meteo.nom, "weather_data": weather_data}, 200

#Ajout de la resource lorsqu'on tape une URL spécifique (/weather)
api.add_resource(MeteoUtilisateur, '/utilisateur/<string:nom_utilisateur>/weather')

# Route pour la page de connexion
@app.route('/', methods=['GET', 'POST'])
def login():
    #si la méthode du request est POST, alors on récupère les données. Sinon, on le retourne sur la même page de connexion (index.html)
    if request.method == 'POST':
        #Alors on récupère le login et le mdp que l'utilisateur a mis dans index.html
        nom_utilisateur = request.form.get('nom')
        mot_de_passe = request.form.get('mdp')

        #Si les identifant son correxte, alors on le redirige vers la page utilisateur (utilisateur.html)
        if verifier_identifiants(nom_utilisateur, mot_de_passe):
            return redirect(url_for('utilisateur', nom=nom_utilisateur))
        #Sinon, on retourne une erreur
        else:
            return "Identifiant faux"
    
    else:
        return render_template('index.html')

# Route pour la page utilisateur
@app.route('/utilisateur/<nom>')
def utilisateur(nom):

    #Récupération des données de l'utilisateur dans la BDD
    utilisateur = Connexion.query.filter_by(nom=nom).first()
    #Si il ne trouve pas l'utilisateur dans la BDD, alors on envoi une erreur
    if not utilisateur:
        return "Utilisateur non trouvé"

    #Pareil mais pour la météo
    meteo = Meteo.query.get(utilisateur.id_meteo)
    if not meteo:
        return "Information météo non disponible"

    #Récupération des données météologiques à partir de l'API (création du lien avec ce qui est dans la table meteo)
    #Pareil que la classe MeteoUtilisateur
    url = f'{meteo.geoapi}appid={meteo.api}&units=metric'
    response = requests.get(url)
    weather_data = response.json()

    #Pagination et tri des notes de l'utilisateur

    page = request.args.get('page', 1, type=int)
    #Récupère le paramètre 'search_query' à partir de la requête HTTP.
    search_query = request.args.get('search_query', '')

    # Filtrage par titre
    notes_query = Notes.query.filter(Notes.id_connexion == utilisateur.id)
    if search_query:
        notes_query = notes_query.filter(Notes.titre.ilike(f"%{search_query}%"))

    # Tri des notes (descendant ou ascendant)
    sort_order = request.args.get('sort_order', 'desc')
    if sort_order == 'desc':
        notes_query = notes_query.order_by(Notes.date.desc())
    else:
        notes_query = notes_query.order_by(Notes.date.asc())

    # Récupération des notes paginées (4 notes max par page)
    notes = notes_query.paginate(page=page, per_page=4)

    #retourne les valeurs a la page utilisateur.html
    return render_template('utilisateur.html', nom_utilisateur=nom, weather_data=weather_data, ville=meteo.nom, notes=notes)

def verifier_identifiants(nom_utilisateur, mot_de_passe):
    utilisateur = Connexion.query.filter_by(nom=nom_utilisateur, mdp=mot_de_passe).first()
    return utilisateur is not None

# Route pour la création d'une note
@app.route('/utilisateur/<nom>/creer-note', methods=['GET', 'POST'])
def creer_note(nom):
    if request.method == 'POST':
        titre = request.form['titre']
        message = request.form['message']

        # Récupère l'utilisateur
        utilisateur = Connexion.query.filter_by(nom=nom).first()

        # Création d'une nouvelle note
        nouvelle_note = Notes(titre=titre, message=message, id_connexion=utilisateur.id)

        try:
            # Ajout de la note à la base de données
            db.session.add(nouvelle_note)
            #envoi dans la BDD
            db.session.commit()
            #Retourne l'utilisateur sur la même page où il est (utilisateur.html)
            return redirect(url_for('utilisateur', nom=nom))
        except:
            #sinon retourne une erreur
            return 'Une erreur s\'est produite lors de la création de la note'

    else:
        #Affichage du formulaire de création de note si la méthode est GET (creer_note.html n'existe pas, ce return existe pour éviter une erreur dans mon code)
        return render_template('creer_note.html', nom_utilisateur=nom)

# Route pour la modification d'une note
@app.route('/utilisateur/<nom>/modifiernote', methods=['GET', 'POST'])
def modifier_note(nom):
    if request.method == 'POST':
        titre = request.form.get('titre')
        ancien_message = request.form.get('ancien_message')
        nouveau_message = request.form.get('message')

        # Recherche de l'utilisateur dans la BDD
        utilisateur = Connexion.query.filter_by(nom=nom).first()
        if utilisateur:
            # Recherche de la note correspondante
            note = Notes.query.filter_by(titre=titre, message=ancien_message, id_connexion=utilisateur.id).first()
            if note:
                # Mise à jour du message de la note
                note.message = nouveau_message
                db.session.commit()
                return redirect(url_for('utilisateur', nom=nom))
            else:
                #retourne une erreur si la note n'est pas trouvé
                return "Note non trouvée"
        else:
            #retourne une erreur si l'utilisateur n'est pas trouvé
            return "Utilisateur non trouvé"
    else:
        #Affichage du formulaire de modification de note si la méthode est GET (pareil pour creer_note.html)  
        return render_template('modifier_note.html')

# Route pour la suppression d'une note    
@app.route('/utilisateur/<nom>/supprimer-note', methods=['GET', 'POST'])
def supprimer_note(nom):
    if request.method == 'POST':
        titre = request.form.get('titre')

        utilisateur = Connexion.query.filter_by(nom=nom).first()
        if utilisateur:
            # Recherche de la note correspondante par le titre
            note = Notes.query.filter_by(titre=titre, id_connexion=utilisateur.id).first()
            #Si note trouvée
            if note:
                # Supprime la note dans la BDD
                db.session.delete(note)
                db.session.commit()
                return redirect(url_for('utilisateur', nom=nom))
            else:
                return "Note non trouvée"
        else:
            return "Utilisateur non trouvé"
    else:
        return render_template('supprimer_note.html')

#Exécution de Flask
if __name__ == '__main__':
    #Création de toutes les tables dans la BDD si elles n'existent pas
    with app.app_context():
        db.create_all()
    #Lancement de Flask en mode débogage
    app.run(debug=True)