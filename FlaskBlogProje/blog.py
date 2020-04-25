from flask import Flask, render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators,Field,ValidationError
from passlib.hash import sha256_crypt
from functools import wraps
from time import time
class RegisterForm(Form):
    name = StringField("İsim Soyisim", validators=[validators.Length(min = 4, max = 25)])
    username = StringField("Kullanıcı adı", validators=[validators.Length(min = 4, max = 10), validators.InputRequired("Please write your username")])
    email = StringField("Email Adresi", validators=[validators.Length(min = 5, max = 20), validators.email(message= "Lütfen geçerli bir e-mail adresi giriniz."), validators.InputRequired("Please write your email")])
    password = PasswordField('New Password', validators = [validators.Length(min = 5, max = 20), validators.InputRequired("Please write your password"), validators.EqualTo('confirm', message='Passwords must match')])
    confirm = PasswordField("Parola Doğrula")

class ArticleForm(Form):
    title = StringField("Article Title", validators=[validators.length(min = 5, max = 100)])
    content = TextAreaField("Article Content", validators=[validators.length(min = 50, max = 5000)])

class LoginForm(Form):
    username = StringField("Username")
    password = PasswordField("Password")

#kullanıcı giriş decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Please log in if you desire to view this page.", "danger")
            return redirect(url_for("about_"))
    return decorated_function

#session true'iken giris yapmak
def login_already(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            flash("You already logged in", "danger")
            return redirect(url_for("about_")) 
                     
        else:
             return f(*args, **kwargs)        
    return decorated_function




app = Flask(__name__)
app.secret_key = "muratblog"
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "murat_blog"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"
mysql = MySQL(app)


@app.route('/calinti')
def calinti_():
    return render_template('Çalıntı_Proje/hirsiz.html')
    

@app.route('/')
def about_():
   return render_template("index.html")


@app.route('/signin', methods = ["GET", "POST"])
@login_already
def sign_in():
    form = LoginForm(request.form)
    if request.method == "POST":
        username = form.username.data
        password_entered = form.password.data
        cursor = mysql.connection.cursor()
        sorgu = "SELECT * FROM user WHERE username = %s"
        result = cursor.execute(sorgu, (username, ))
        if result > 0:
            data = cursor.fetchone()
            real_password = data["password"]
            if sha256_crypt.verify(password_entered, real_password):
                flash("Login Successfully", "success")
                session["logged_in"] = True
                session["username"] = username
                return redirect(url_for('about_'))
                
            else:
                flash('Password incorrect. Check your password', 'danger')
                return redirect(url_for("sign_in"))
                
        else:
            flash("Username is invalid", "danger")
            return redirect(url_for("sign_in"))

    else:
        return render_template("login.html", form = form) 

@app.route('/logout')        
def logout():
    session.clear()
    return redirect(url_for("about_"))
    

@app.route('/dashboard')
@login_required        
def dashboard():
    cursor = mysql.connection.cursor()
    sorgu = "SELECT * FROM articles WHERE author = %s"
    result = cursor.execute(sorgu, (session["username"], ))
    if result > 0:
        data = cursor.fetchall()
        return render_template("dashboard.html", data = data)
    else:
        flash("You haven't got any articles yet.")
        return render_template("dashboard.html")

@app.route('/signup', methods = ["GET", "POST"])
@login_already
def register():
    form = RegisterForm(request.form) #sayfamıza request yapılınca bu formu göndericez
    if request.method == "POST" and form.validate():
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)
        
        
        cursor = mysql.connection.cursor()
        sorgu = "INSERT INTO user(name, email, username, password) VALUES(%s, %s, %s, %s)"
        cursor.execute(sorgu,(name, email, username, password))
        mysql.connection.commit()
        cursor.close()
        flash("Sign Up Succesfully, Welcome To the my blog !", "success")
        return redirect(url_for("sign_in"))

    else:
        return render_template("register.html", form = form) 
        
#Makale Ekleme
@app.route("/addarticle", methods = ["GET", "POST"])
@login_required
def add_article():
    form = ArticleForm(request.form)
    if request.method == "POST" and form.validate():
        title = form.title.data
        content = form.content.data

        cursor = mysql.connection.cursor()
        sorgu = "INSERT INTO articles(title, author, content) VALUES(%s, %s, %s)"
        cursor.execute(sorgu,(title, session["username"], content))
        mysql.connection.commit()
        cursor.close()
        flash("Your article uploaded succesfully", "success")
        return redirect(url_for("about_"))
    
    return render_template("addarticles.html", form = form)

#dashboard sayfası
@app.route("/articles")
def show_articles():
    cursor = mysql.connection.cursor()
    sorgu = "SELECT * FROM articles"
    result = cursor.execute(sorgu)
    if result > 0:
        articles = cursor.fetchall()
        return render_template("articles.html", articles = articles)
    else:
        return render_template("articles.html")

#detay sayfası
@app.route("/article/<string:id>")
def article(id):
    cursor = mysql.connection.cursor()
    sorgu = "SELECT * FROM articles WHERE id = %s"
    result = cursor.execute(sorgu, (id, ))
    if result > 0:
        article = cursor.fetchone()
        return render_template ('article.html', article = article)
    else:
        return render_template('article.html')

@app.route('/delete/<string:id>')
@login_required
def article_delete(id):
    cursor = mysql.connection.cursor()
    sorgu = 'DELETE FROM articles WHERE id = %s'
    result = cursor.execute(sorgu, (id,))
    mysql.connection.commit()
    cursor.close()
    flash('Article removed from database', 'success')
    return redirect(url_for('dashboard'))

@app.route('/edit/<string:id>', methods = ["GET", "POST"])
@login_required
def article_update(id):
    if request.method == 'GET':
        cursor = mysql.connection.cursor()
        sorgu = 'SELECT * FROM articles WHERE id = %s and author = %s'
        result = cursor.execute(sorgu, (id, session['username']))
        if result == 0:
            flash("You don't have permisson to update this article", "danger")
            cursor.close()
        else:
            article = cursor.fetchone()
            form = ArticleForm()
            form.title.data = article['title']
            form.content.data = article['content']
            cursor.close()
            return render_template("update.html", form = form)
    else:
        form = ArticleForm(request.form)
        newtitle = form.title.data
        newcontent = form.content.data
        cursor = mysql.connection.cursor()
        sorgu2 = "UPDATE articles SET title = %s, content = %s WHERE id = %s"
        cursor.execute(sorgu2, (newtitle, newcontent, id))
        mysql.connection.commit()
        cursor.close()
        flash("Article updated", "success")
        return redirect(url_for("dashboard"))


@app.route("/search", methods = ["GET", "POST"])
def search():
    if request.method == "GET":
        return redirect(url_for("about_"))
    else:
        keyword = request.form.get("keyword")
        cursor = mysql.connection.cursor()
        sorgu = "SELECT * FROM articles WHERE title LIKE '%" + keyword + "%' "
        result = cursor.execute(sorgu)
        
        if result == 0:
            flash("There's no such a article with those keywords...", "warning")
            return redirect(url_for("show_articles"))
        else:
            articles = cursor.fetchall()
            return render_template("articles.html", articles = articles)




if __name__ == "__main__":

    app.run(debug=True)