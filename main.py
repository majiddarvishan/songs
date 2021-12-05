import json
from flask import Flask, request, jsonify
from flask_mongoengine import MongoEngine
from mongoengine.errors import ValidationError
from werkzeug.utils import append_slash_redirect

app = Flask(__name__)
app.config['MONGODB_SETTINGS'] = {
    'db': 'songs',
    'host': 'localhost',
    'port': 27017
}

db = MongoEngine()
db.init_app(app)

class Song(db.Document):
    song_id = db.SequenceField(required=True, unique=True)
    artist = db.StringField(required=True)
    title = db.StringField(required=True)
    difficulty = db.FloatField(required=True)
    level = db.IntField(required=True)
    released = db.DateTimeField(required=True,format="%Y-%m-%d")
    rating = db.IntField(db_field='rating', min_value=1, max_value=5, default=1)

    def to_json(self):
        return {"song_id" : self.song_id,
                "artist" : self.artist,
                "title" : self.title,
                "difficulty" : self.difficulty,
                "level" : self.level,
                "released" :  self.released,
                "rating" :  self.rating}

@app.route('/', methods=['GET'])
def query_records():
    page = request.args.get('page', None)
    per_page = request.args.get('per_page', None)

    if page != None:
        songs = Song.objects.paginate(page=int(page), per_page=int(per_page))
        if not songs:
            return jsonify({'error': 'data not found'})
        else:
            return jsonify([s.to_json() for s in songs.items])
    else:
        songs = Song.objects.all()
        if not songs:
            return jsonify({'error': 'data not found'})
        else:
            return jsonify([s.to_json() for s in songs])

@app.route('/difficulty', methods=['GET'])
def query_difficulty():
    level = request.args.get('level', None)

    if level != None:
        songs = Song.objects(level=level).all()
        if not songs:
            return jsonify({'error': 'data not found'})
        else:
            return jsonify([s.to_json() for s in songs])
    else:
        avg = Song.objects.average("difficulty")
        return jsonify({'average': avg})

@app.route('/search', methods=['GET'])
def query_search():
    message = request.args.get('message', None)
    if not message:
        return jsonify({'error': 'error in query'})
    else:
        songs = Song.objects(artist__icontains=message).all()
        if len(songs):
            return jsonify([s.to_json() for s in songs])
        else:
            songs = Song.objects(title__icontains=message).all()
            return jsonify([s.to_json() for s in songs])

@app.route('/', methods=['PUT'])
def create_record():
    record = json.loads(request.data)
    song = Song(artist= record["artist"],
                title= record["title"],
                difficulty= record["difficulty"],
                level= record["level"],
                released= record["released"])
    song.save()
    return jsonify(song.to_json())

@app.route('/', methods=['POST'])
def update_record():
    record = json.loads(request.data)
    song = Song.objects(song_id=record['song_id']).first()
    if not song:
        return jsonify({'error': 'data not found'})
    else:
        try:
            song.update(rating=record['rating'])
            return jsonify(song.to_json())
        except ValidationError as exp:
            print(exp)
            return jsonify({'error': exp.message})

if __name__ == "__main__":
    app.run(debug=True)