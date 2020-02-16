from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def hello_word():
    return 'Hello World';


@app.route('/super_simple')
def super_simple():
    #returning valid JSON key:value pairs
    return jsonify(message='Hello from the Planetary API.'), 200


@app.route('/not_found')
def not_found():
    #returning valid JSON key:value pairs
    return jsonify(message='That Resource was not found'), 404


if __name__ == '__main__':
    app.run()