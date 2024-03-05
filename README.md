# MesNotes 📝
![](./documentation/logo_mesnotes_en_jpg.jpg)

MesNotes une interface utilisateur qui permet de créer, modifier ou supprimer des notes (posthite numérique).

## 🌟 Caractéristiques

- **Créer, modifier ou supprimer de(s) note(s)**
- **Filtrer vos notes**
- **Voir la météo de votre ville**

## Installation

1. Installer git
```sudo apt-get install git```
2. Cloner le projet
```git clone https://github.com/GCpas/MesNotes.git && cd MesNotes``` ou ```git clone git@github.com:GCpas/MesNotes.git && cd MesNotes```
3. Installer python3, pip et virtualenv
```sudo apt-get install python3 python3-pip python3-virtualenv```
4. Créer le dossier .venv
```sudo virtualenv -p python3 .venv```
5. Activer la virtualisation
```source .venv/bin/activate```
6. Installer Flask, SQLAlchemy, Flask-RESTful et requests
```sudo pip install Flask```
```sudo pip install Flask-sqlalchemy```
```sudo pip install Flask-RESTful```
```sudo pip install requests```
7. Lancer le programme python
```sudo python3 MesNotes.py```
8. Ouvrer un navigateur et taper **127.0.0.1:5000** (c'est l'adresse par défaut).
9. Entrez votre login (voir le document login.txt, dans le dossier documentation).
10. **Profiter 😀 !**

## 📝 Structuration du projet

Pour voir comment le projet à été penser, **tout est dans le dossier documentation !**