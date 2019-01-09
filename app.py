from datetime import datetime

from flask import Flask

from pymongo import MongoClient, ASCENDING, DESCENDING
client = MongoClient()
db = client.poento

from pymongo.collection import ReturnDocument

from bson.objectid import ObjectId

from flask import Flask, request, jsonify, send_from_directory

from cerberus import Validator

from data import COUNTRIES

app = Flask(__name__)


@app.route('/v1/scores', methods=['POST'])
def save_score():
    if not request.is_json:
        return jsonify({'status': 415, 'message': 'it_is_not_JSON'}), 415
    j = request.get_json()
    schema = {
        'country': {
            'required': True,
            'type': 'string',
            'minlength': 2,
            'maxlength': 3
        },
        'name': {
            'required': True,
            'type': 'string',
            'maxlength': 36,
            'minlength': 1
        },
        'value': {
            'required': True,
            'type': 'integer',
            'min': 1,
            'max': 20000
        }
    }
    V = Validator(schema)
    if not V.validate(j):
        return jsonify({
            'status': 400,
            'errors': V.errors,
            'message': 'invalid_format'
        }), 400

    j['datetime'] = datetime.utcnow()

    db.scores.insert_one(j)

    return jsonify({'status': 201}), 201


@app.route('/v1/scores')
def show_scores():
    country = request.args.get('country', default='', type=str)
    skip = request.args.get('skip', default=0, type=int)
    limit = request.args.get('limit', default=10, type=int)
    period = request.args.get('period', default='all', type=str)

    if skip < 0 or limit < 0 or len(country) > 3 or period not in [
            'day', 'week', 'month', 'year', 'all'
    ] or country not in COUNTRIES:
        return jsonify({'status': 400, 'message': 'invalid_format'}), 400

    filter_ = {}
    if country != '':
        filter_['country'] = country
    scores = db.scores.find(filter_).sort('value',
                                            DESCENDING).skip(skip).limit(limit)

    for score in scores:
        score['_id'] = str(score['_id'])

    return jsonify({'status': 200, 'scores': scores}), 200


if __name__ == '__main__':
    app.run()