from flask import Flask, render_template

app = Flask(__name__, 
            static_folder='app/static', 
            template_folder='app/templates')

@app.route('/')
def dashboard():
    return "Dashboard Fotolibro AI: Sistema Pronto."

if __name__ == '__main__':
    app.run(debug=True, port=5000)
