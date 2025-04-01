from flask import Flask, render_template, request, redirect, url_for
app = Flask(__name__)

@app.route('/')
def userlogin():
    return render_template('userlogin.html')

@app.route('/managerlogin')
def managerlogin():
    return render_template("managerlogin.html")

@app.route("/register")
def register():
    return render_template('register.html')
if __name__ == '__main__':
    app.run(debug=True)