from flask import Flask, render_template, request, redirect, flash, session, escape
from flask_sqlalchemy import SQLAlchemy #--> libreria de base de datos
from werkzeug.security import generate_password_hash, check_password_hash #--> libreria para cifrar contrasenias
import sqlite3
import os
from time import gmtime, strftime

dbdir = "sqlite:///" + os.path.abspath(os.getcwd()) + "/database.db" # "os.path.abspath(os.getcwd())" genera ruta de trabajo actual

app = Flask(__name__)
app.jinja_env.trim_blocks = True # para que el html se vea bien identado
app.secret_key = 'xzZ7W9LtLQk$hMbP'
app.config["SQLALCHEMY_DATABASE_URI"] = dbdir # ruta de la base de datos
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app) #--> Creacion de la base de datos en programa

class Users(db.Model): # esquema de base de datos con clase de python
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(90), nullable=False)
    mac = db.Column(db.String(20), nullable=False)

class Data(db.Model): # esquema de base de datos con clase de python
    id = db.Column(db.Integer, primary_key=True)
    names = db.Column(db.String(20), nullable=False)
    temps = db.Column(db.String(5), nullable=False)
    mac = db.Column(db.String(20), nullable=False)
    hora = db.Column(db.String(20), nullable=False)

@app.route("/") # index/home
def index():
  if "username" in session: # detectar si el usuario esta logueado
    flash("%s"% escape (session["username"]), "username") # mostrar el nombre del usuario en la pagina con la clase username
    return render_template("indexl.html")
  else:
    return render_template("index.html")

@app.route("/signup/", methods=["GET", "POST"] ) # seccion de logueo //get
def signup():
  if "username" in session:
    return redirect("/")
  else:
    if request.method == "POST": # si el metodo que recibimos es de tipo post
      if request.form["username"] != '':
        user = Users.query.filter_by(username=request.form["username"]).first()
        if user: # consultamos si hay un usuario con esa cuenta
          flash("Ese usuario ya existe, intenta con otro", "error") # mostramos un mensaje tipo flash con una clase asignada para luego poder ponerle color con css
        else:
          if request.form["password"] != '':
            if request.form["password"] == request.form["password2"]:
              hashed_pw = generate_password_hash(request.form["password"], method="sha256") # recibe la contrasenia que ingreso el usuario y la cifra usando la libreria "werkzeug.security"
              new_user = Users(username=request.form["username"], password=hashed_pw, mac=0) # creamos el usuario
              db.session.add(new_user)
              db.session.commit()
              flash("Registrado correctamente, inicia sesion para ingresar!", "success")
              return redirect("/login/") #redireccionamiento hacia a la pagina de logueo
            else:
              flash("Las contraseñas deben ser iguales.", "error")
          else:
            flash("Debe ingresar una contraseña valida.", "error")
      else:
        flash("Debe ingresar un usuario.", "error")
    return render_template("signup.html")


@app.route("/login/", methods=["GET", "POST"])
def login():
  if "username" in session:
    return redirect("/")
  else:
    if request.method == "POST":
        user = Users.query.filter_by(username=request.form["username"]).first() # busca en los usuarios en la database y elige el primero
        if user:
          if check_password_hash(user.password, request.form["password"]): # si el nombre de usuario existe, coompara las contrasenias con check_password_hash
            session["username"] = user.username
            return redirect("/")
          else:
            flash("Contraseña incorrecta.", "error")
        else:
          flash("El usuario ingresado no existe.", "error")
    return render_template("login.html")

@app.route("/logout")
def logout():
  session.pop("username", None) #session.pop(username) sirve para desloguear, el none es para que no haya errores si no encuentra la cookie que queremos borrar
  return redirect("/")
  
@app.route("/about-us/") # 
def aboutus():
  if "username" in session: # detectar si el usuario esta logueado
    flash("%s"% escape (session["username"]), "username") # mostrar el nombre del usuario en la pagina con la clase username
    return render_template ("aboutusl.html")
  else:
    return render_template ("aboutus.html")
@app.route("/FAQ/")
def FAQ():
  return render_template("faq.html")

@app.route("/client/", methods=["GET", "POST"])
def client():
  if "username" in session: # detectar si el usuario esta logueado
    query1 = """SELECT mac FROM Users WHERE username = '{}' """.format(session["username"])
    connection = sqlite3.connect('database.db')
    cursor = connection.cursor()
    cursor.execute(query1)
    mac = cursor.fetchone()#cursor.fetchone() method returns a single record or None if no more rows are available.
    connection.commit()
    if mac[0] == '0':#ultilizamos mac[0] ya que el comando cursor.fetchone//fetchall devuelven una lista y cada segmento tiene un nombre (1,2,3)
      if request.method == "POST":
        if request.form["mac"] == request.form["mac2"]:
          query = """UPDATE Users SET mac = '{}' WHERE username = '{}'""".format(request.form["mac"], session["username"])
          connection = sqlite3.connect('database.db')
          cursor = connection.cursor()
          cursor.execute(query)
          connection.commit()
          return redirect("/data-view")
        else:
          flash("Las MACs deben ser iguales.", "error")
      return render_template("client.html")
    elif mac[0] == 'None':
        return redirect("/loguot")
    else: 
      return redirect ("/data-view")
  else:
    flash("Debes inciar sesion para acceder a esta zona.", "error")
    return redirect("/login/")

@app.route("/data-view", methods=["GET", "POST"])
def search():
#https://stackoverflow.com/questions/31431393/unrecognized-token-in-sqlite-statement
  if "username" in session: # detectar si el usuario esta logueado
    query1 = """SELECT mac FROM Users WHERE username = '{}'""".format(session["username"])
    connection = sqlite3.connect('database.db')
    cursor = connection.cursor()
    cursor.execute(query1)
    maac = cursor.fetchone()
    if maac[0]=='0':
      flash("Debes tener una mac registrada para acceder aqui.", "error")
      return redirect("/client/")
    else:
      query = """SELECT names, temps, hora FROM Data WHERE mac = (?) order by id DESC;"""#crear comando para requerir los datos "names, temps y mac" a la tabla "Data"
      connection = sqlite3.connect('database.db')
      cursor = connection.cursor()
      cursor.execute(query, (str(maac[0]), ))
      rows = cursor.fetchall()#almacenamos los valores en una variable/ lista
      connection.commit()

      inicio=0
      final=10
      s=0
      dta= len(rows)
      data= len(rows)
      pages=1
      while s==0:
        if dta > 10:
          dta= dta - 10
          pages= pages + 1
        else:
          s=1
          print("paginas= {}".format(pages))
      if pages>1:
        if request.args.get('page'):
            print("A")
            a= True
            cantidad=int(request.args.get('page'))
            while a == True:
              if data>10:
                if cantidad>1:
                  inicio= inicio+10
                  final= final+10
                  data=data-10
                  cantidad= cantidad-1
                else:
                  a= False
                  for i in range(inicio, final):
                    flash(rows[i], "table")
              else:
                if cantidad>1:
                  inicio= inicio+10
                  final= final+data
                  data=data-10
                  cantidad= cantidad-1
                else:
                  a= False
                  for i in range(inicio, final):
                    try:
                      flash(rows[i], "table")
                    except:
                      print("out of range({})".format(i))
        else:
          for i in range(0, 10):
            flash(rows[i], "table")
        pgs = []
        for i in range(1, pages+1):
          pgs.append(i) 
        flash(pgs, "paginas")
      else:
        for row in rows: # recorreremos la variable e imprimiremos todos los valores.
          flash(row, "table")
      if request.method == "POST":
        if request.form['boton'] == 'CMac':
          query = """UPDATE Users SET mac = '0' WHERE username = '{}'""".format(session["username"])
          connection = sqlite3.connect('database.db')
          cursor = connection.cursor()
          cursor.execute(query)
          connection.commit()
          flash("Borraste tu mac, vuelve a ingresar tu mac para acceder.", "error")
        return redirect("/client/")
      return render_template ("test.html")
  else:
    flash("Debes inciar sesion para acceder a esta zona.", "error")
    return redirect("/login/")

@app.route("/datos", methods=["GET", "POST"])
def datosa():
    dato = Data(names=request.args.get('name'), temps=request.args.get('temp'),mac=request.args.get('mac'),hora=strftime("%H:%M %d-%m", gmtime())) # creamos el usuario
    db.session.add(dato)
    db.session.commit()
    return'''<h1>Dato registrado!</h1><br/>'''

@app.route("/test2/", methods=["GET", "POST"])
def test():
    connection = sqlite3.connect('database.db')
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM Users')
    rows = cursor.fetchall()#almacenamos los valores en una variable/ lista
    cursor.execute('SELECT * FROM Data')
    rows2 = cursor.fetchall()#almacenamos los valores en una variable/ lista
    return '''<h2>datos de la tabla Users=</h2><p>{}</p><h2>datos de la tabla Data=</h2><p>{}</p>'''.format(rows, rows2)

if __name__ == "__main__":
  db.create_all() # crear la base de datos(SI NO ESTA CREADA)
  app.run(debug=True)