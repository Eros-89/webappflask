from flask import Flask, request, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

import json
import requests


# Creazione oggetto app
app = Flask(__name__)

# Configurazione
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Creatures.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Connessione db
db = SQLAlchemy(app)
migrate = Migrate(app, db)



class Pokemon(db.Model):
    id     = db.Column(db.Integer, primary_key=True)
    name   = db.Column(db.Text, nullable=False)
    height = db.Column(db.Integer, nullable=True)
    weight = db.Column(db.Integer, nullable=True)
    types  = db.Column(db.Text, nullable=True)  
    stats  = db.Column(db.Text, nullable=True)  


class Creature:

    def __init__(self, **data_dict):
        self.id     = data_dict.get("id")
        self.name   = data_dict.get("name")
        self.height = data_dict.get("height")
        self.weight = data_dict.get("weight")
        self.types  = data_dict.get("types")
        self.stats  = data_dict.get("stats")



class PokemonReader:

    def fetch_as_dict(self, name_or_id):

        url = f"https://pokeapi.co/api/v2/pokemon/{name_or_id}"

        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            original_data = response.json()

            list_types = []
            for element in original_data.get("types", []):
                list_types.append(element["type"]["name"])

            dict_stats = {}
            for key in original_data.get("stats", []):
                dict_stats[key["stat"]["name"]] = key["base_stat"]

            return {
                "id":     original_data.get("id"),
                "name":   original_data.get("name"),
                "height": original_data.get("height"),
                "weight": original_data.get("weight"),
                "types":  list_types,
                "stats":  dict_stats
            }

        except requests.exceptions.ConnectionError:
            return None

        except requests.exceptions.HTTPError:
            return None

        except requests.exceptions.ConnectTimeout:
            return None
        


@app.route('/')
def index():
    pokemons = Pokemon.query.all()
    return render_template('index.html', pokemons=pokemons)



@app.route('/add', methods=['GET', 'POST'])
def add_pokemon():

    if request.method == 'POST':

        name = request.form['name_pokemon'].strip().lower()

        reader = PokemonReader()
        data = reader.fetch_as_dict(name)
        if data is None:
            return render_template('add.html', error=f"Pokémon '{name}' non trovato o errore di connessione.")

        new_pokemon = Pokemon(
            id     = data['id'],
            name   = data['name'],
            height = data['height'],
            weight = data['weight'],
            types  = json.dumps(data['types']), 
            stats  = json.dumps(data['stats'])   
        )

        db.session.add(new_pokemon)
        db.session.commit()

        return redirect(url_for('index'))

    return render_template('add.html', error=None)


@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_pokemon(id):

    pokemon = Pokemon.query.get_or_404(id)

    if request.method == 'POST':
        pokemon.height = int(request.form['height'])
        pokemon.weight = int(request.form['weight'])

        db.session.commit() 

        return redirect(url_for('index'))

    return render_template('edit.html', pokemon=pokemon)


if __name__ == '__main__':
    app.run(debug=True)

