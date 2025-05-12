from flask import Flask, render_template, request
from youtube import get_quotes
app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/results')
def results():
    return get_quotes(request.args.get('query'), request.args.get('quote'))

@app.route('/search')
def search():
    context = {"query": request.args.get('query'), "quote":  request.args.get('quote') }
    return render_template('index.html', **context)

if __name__ == '__main__':
    app.run(debug=True)
