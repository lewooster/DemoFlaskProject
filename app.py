from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Float
from flask_marshmallow import Marshmallow
import os
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
from flask_mail import Mail, Message

app = Flask(__name__)

# sql alchemy config
# using DB browser for SQLite
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'+os.path.join(basedir, 'planets.db')

# JWT config variable
app.config['JWT_SECRET_KEY'] = 'super-secret'  # change this later

# Mail trap config
app.config['MAIL_SERVER']=os.environ['MAIL_SERVER']
app.config['MAIL_PORT'] = os.environ['MAIL_PORT']
app.config['MAIL_USERNAME'] = os.environ['MAIL_USERNAME']
app.config['MAIL_PASSWORD'] = os.environ['MAIL_PASSWORD']
app.config['MAIL_USE_TLS'] = os.environ['MAIL_USE_TLS']
app.config['MAIL_USE_SSL'] = os.environ['MAIL_USE_SSL']

# Instantiates SQLite db
db = SQLAlchemy(app)

# Instantiates Marshmallow
ma = Marshmallow(app)

# Initialise JWT manager
jwt = JWTManager(app)

# Initialise Mail Server
mail = Mail(app)


# Flask CLI commands
# create db
@app.cli.command('db_create')  # flask db_create
def db_create():
    db.create_all()
    print('Database Created!')


@app.cli.command('db_drop')  # flask db_drop
def db_drop():
    db.drop_all()
    print('Database dropped!')


@app.cli.command('db_seed')  # flask db_seed
def db_seed():
    mercury = Planet(planet_name='Mercury',
                     planet_type='Class D',
                     home_star='Sol',
                     mass=3.258e23,
                     radius=1516,
                     distance=35.98e6)

    venus = Planet(planet_name='Venus',
                   planet_type='Class K',
                   home_star='Sol',
                   mass=4.867e24,
                   radius=3760,
                   distance=67.24e6)

    earth = Planet(planet_name='Earth',
                   planet_type='Class M',
                   home_star='Sol',
                   mass=5.972e24,
                   radius=3959,
                   distance=92.96e6)

    db.session.add(mercury)
    db.session.add(venus)
    db.session.add(earth)

    test_user = User(first_name='William',
                     last_name='Herschel',
                     email='test@test.com',
                     password='P@ssw*rd')

    db.session.add(test_user)
    db.session.commit()
    print('Database seeded!')


@app.route('/')
def hello_word():
    return 'Hello World'


@app.route('/super_simple')
def super_simple():
    # returning valid JSON key:value pairs
    return jsonify(message='Hello from the Planetary API.'), 200


@app.route('/not_found')
def not_found():
    # returning valid JSON key:value pairs
    return jsonify(message='That Resource was not found'), 404


@app.route('/parameters')
def parameters():
    name = request.args.get('name')
    age = int(request.args.get('age'))
    if age < 18:
        return jsonify(message='Sorry '+name+', you are not old enough'), 401
    else:
        return jsonify(message='Welcome '+name+' you are old enough'), 200


@app.route('/url_variables/<string:name>/<int:age>')
def url_variables(name: str, age: int):
    if age < 18:
        return jsonify(message='Sorry '+name+', you are not old enough'), 401
    else:
        return jsonify(message='Welcome '+name+' you are old enough'), 200


@app.route('/planets', methods=['GET'])  # only responds to GET requests
def planets():
    planets_list = Planet.query.all()
    result = planets_schema.dump(planets_list)
    return jsonify(result)

# authentication workflow
# form URL encoded input
@app.route('/register', methods=['POST'])
def register():
    email = request.form['email']
    # email lookup against db to check if email exists
    test = User.query.filter_by(email=email).first()
    if test:
        return jsonify(message='That email already exists'), 409  # conflict
    else:
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        password = request.form['password']
        user = User(first_name=first_name, last_name=last_name, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        return jsonify(message="User created successfully"), 201


# Login JWT route

@app.route('/login', methods=['POST'])
def login():
    if request.is_json: # detects json encoded POST
        email = request.json['email']
        password = request.json['password']
    else:
        email = request.form['email']
        password = request.form['password']

    test = User.query.filter_by(email=email, password=password).first()
    if test:
        access_token = create_access_token(identity=email)
        return jsonify(message='Login succeeded', access_token=access_token)
    else:
        return jsonify(meesage='Bad email or password'), 401


# Email user
@app.route('/retrieve_password/<string:email>', methods=['GET'])
def retrieve_password(email: str):
    user = User.query.filter_by(email=email).first()
    if user:
        msg = Message('your planetary api password is ' + user.password,
                      sender="admin@planatary-api.com",
                      recipients=[email])

        mail.send(msg)
        return jsonify(message='Password sent to ' + email), 200
    else:
        return jsonify(message='That email doesnt exist'), 401

# Detail route
@app.route('/planet_details/<int:planet_id>', methods=['GET'])
def planet_details(planet_id: int):
    planet = Planet.query.filter_by(planet_id=planet_id).first()
    if planet:
        result = planet_schema.dump(planet)
        return jsonify(result), 201
    else:
        return jsonify(message = 'That planet does not exist'), 404


# add planets
@app.route('/add_planet', methods=['POST'])
@jwt_required  # protecting endpoint with JWT
def add_planet():
    planet_name = request.form['planet_name']
    test = Planet.query.filter_by(planet_name=planet_name).first()
    if test:
        return jsonify(message = "There is already a planet by that name"), 409
    else:
        planet_type = request.form['planet_type']
        home_star = request.form['home_star']
        mass = float(request.form['mass'])
        radius = float(request.form['radius'])
        distance = float(request.form['distance'])

        new_planet = Planet(planet_name=planet_name, planet_type=planet_type,home_star=home_star,mass=mass,radius=radius,distance=distance)

        db.session.add(new_planet)
        db.session.commit()
        return jsonify(message='You added a planet'), 201


# database models
class User(db.Model):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True)
    password = Column(String)


class Planet(db.Model):
    __tablename__ = 'planets'
    planet_id = Column(Integer, primary_key=True)
    planet_name = Column(String)
    planet_type = Column(String)
    home_star = Column(String)
    mass = Column(Float)
    radius = Column(Float)
    distance = Column(Float)


#  Marshmallow serialisation and deserialisation schema
class UserSchema(ma.Schema):
    class Meta:
        fields = ('id', 'first_name', 'last_name', 'email', 'password')


class PlanetSchema(ma.Schema):
    class Meta:
        fields = ('planet_id', 'planet_name', 'planet_type', 'home_star', 'mass', 'radius', 'distance')

#  deserialise single record
user_schema = UserSchema()
#  deserialise multiple records
users_schema = UserSchema(many=True)


#  deserialise single record
planet_schema = PlanetSchema()
#  deserialise multiple records
planets_schema = PlanetSchema(many=True)


if __name__ == '__main__':
    app.run()
