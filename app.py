from flask import Flask, send_from_directory
import os

app = Flask(__name__)

IMAGE_PATH = "/data/nfs/"

@app.route('/')
def home():
    return '<h1 style="color:green;">Task Complete</h1>'

@app.route('/image')
def image():
    return send_from_directory(IMAGE_PATH, 'image.jpg')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

