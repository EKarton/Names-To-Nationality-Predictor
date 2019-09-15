import sys
sys.path.append('../ML Model/src')

from flask import Flask, render_template, request, abort
from names_to_nationality_classifier import NamesToNationalityClassifier
from functools import reduce

def get_countries():
    country_id_to_country_name = {}

    with open('../ML Model/data/countries.csv') as countries_file_reader:

        line = countries_file_reader.readline()
        while line:
            tokenized_line = line.split(',')
            if len(tokenized_line) == 3:
                country_id = int(tokenized_line[0])
                country_name = tokenized_line[1]
                nationality = tokenized_line[2]

                country_id_to_country_name[country_id] = (country_name, nationality)

            line = countries_file_reader.readline()

    return country_id_to_country_name
    
country_id_to_country = get_countries()
countries = [ country_id_to_country[id][0] for id in country_id_to_country ]

# Get the ML model
classifier = NamesToNationalityClassifier(countries)
classifier.load_model_from_file('../ML Model/data/data.npz')

app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    return render_template('home/index.html')
  
@app.route('/nationality', methods=['GET', 'POST'])
def get_nationality():
    if request.method == 'POST':
        name = request.form.get('name')
        country = request.form.get('country')
        print('Fixing prediction for name', name, 'with country', country)
        classifier.train_example(name, country)

        return render_template('fix-nationality-feedback/index.html')

    else:
        name = request.args.get('name')
        print(name)

        if type(name) is not str:
            abort(404)

        name.strip()

        if len(name) == 0:
            return render_template('prediction-error/index.html', error_message='your name cannot be blank.'), 400

        if len(name.split(' ')) <= 1:
            return render_template('prediction-error/index.html', error_message='your name needs to have a last name.'), 400

        predictions = classifier.predict(name)
        most_probable_country = predictions[0][1]

        # Format the predictions so that it is in %
        formatted_predictions = [ 
            (str(round(probability * 100, 2)) + '%', country_name) 
            for probability, country_name in predictions
        ]

        # Capitalize the first and last name
        formatted_name = reduce(lambda x, y: x + ' ' + y, [ token.capitalize() for token in name.split() ])

        return render_template('nationality/index.html', 
            name=formatted_name, 
            most_probable_country=most_probable_country, 
            predictions=formatted_predictions)  

@app.route('/fix-nationality', methods=['GET'])
def fix_nationality():
    name = request.form.get('name')
    incorrect_country = request.form.get('incorrect_country')
    return render_template('fix-nationality/index.html', 
        name=name, 
        countries=countries, 
        incorrect_country=incorrect_country)         

@app.errorhandler(400)
def not_found_error(error):
    return render_template('400.html'), 400

if __name__ == '__main__':
    app.run(debug = True)