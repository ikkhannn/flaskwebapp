from flask import Flask,request,render_template,redirect,flash,url_for,session,logging

from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps

app =  Flask(__name__)

# config MySQL

app.config['MYSQL_HOST']='localhost'
app.config['MYSQL_USER']='root'
app.config['MYSQL_PASSWORD']=''
app.config['MYSQL_DB']='myflaskapp'
app.config['MYSQL_CURSORCLASS']='DictCursor'

# init MYSQL

mysql=MySQL(app)


# Articles=Articles()

@app.route('/')

def index():
    return render_template('home.html')


# about
@app.route('/about')
def about():
    return render_template('about.html')



@app.route('/articles')
def articles():

        cur=mysql.connection.cursor()

        result=cur.execute("SELECT * FROM articles")

        articles=cur.fetchall()

        if(result>0):
            return render_template('articles.html',articles=articles)
        else:
            msg="no articles found"
            return render_template('articles.html',msg=msg)
        cur.close()



# single article
@app.route('/articles/<string:id>/')
def article(id):


    cur=mysql.connection.cursor()

    result=cur.execute("SELECT * FROM articles where id='{}'".format(id))

    article=cur.fetchone()


    return render_template('article.html',article=article)



# register form class
class RegisterForm(Form):
    name=StringField('Name',[validators.Length(min=1,max=50)])
    username=StringField('Username',[validators.length(min=4,max=25)])
    email=StringField('Email',[validators.Length(min=6,max=50)])
    password=PasswordField('Password',[validators.DataRequired(),validators.EqualTo('confirm',message='Passwords do not match')])
    confirm=PasswordField('Confirm password')

@app.route('/register',methods=['GET','POST'])
def register():
    form = RegisterForm(request.form)
    if request.method=='POST' and form.validate():
        name=form.name.data
        email=form.email.data
        username=form.username.data
        password=sha256_crypt.encrypt(str(form.password.data))

        #Create cursor

        cur=mysql.connection.cursor()

        cur.execute("INSERT INTO users(name,email,username,password) VALUES('{}','{}','{}','{}')".format(name,email,username,password))

        # commit to DB

        mysql.connection.commit()
        cur.close()

        flash('You are now registered','success')

        return redirect(url_for('login'))
    return render_template('register.html',form=form)



#user login
@app.route('/login',methods=['GET','POST'])
def login():

    if request.method =='POST':
        # get form fields

        username=request.form['username']
        password_candidate=request.form['password']

        # create cursor

        cur=mysql.connection.cursor()

        #get user by username

        result=cur.execute("Select * FROM users WHERE username ='{} '".format(username))

        if result>0:
            # get stored hash
            data = cur.fetchone()

            password=data['password']

            # compare passswords

            if sha256_crypt.verify(password_candidate,password):
                # passed

                session['logged_in']=True

                session['username']=username

                flash('you are now logged in','success')
                return redirect(url_for('dashboard'))

                session
            else:
                error='invalid login'
                return render_template('login.html',error=error)
                # closed connection
                cur.close()
        else:
            error='Username not found'
            return render_template('login.html',error=error)



    return render_template('login.html')




# check if user logged_in

def is_logged_in(f):
    @wraps(f)
    def wrap(*args,**kwargs):
        if 'logged_in' in session:
            return f(*args,**kwargs)
        else:
            flash('unauthorized please log in','danger')
            return redirect(url_for('login'))
    return wrap

# dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():


    cur=mysql.connection.cursor()

    result=cur.execute("SELECT * FROM articles")

    articles=cur.fetchall()

    if(result>0):
        return render_template('dashboard.html',articles=articles)
    else:
        msg="no articles found"
        return render_template('dashboard.html',msg=msg)
    cur.close()

# article form class

class ArticleForm(Form):
    title=StringField('Title',[validators.Length(min=1,max=200)])
    body=TextAreaField('Body',[validators.length(min=30)])


#add article

@app.route('/add_article',methods=['GET','POST'])
@is_logged_in
def add_article():
    form=ArticleForm(request.form)

    if request.method=='POST' and form.validate():
        title=form.title.data
        body=form.body.data


        # create a cursor

        cur=mysql.connection.cursor()

        cur.execute("INSERT INTO articles(title,body,author) VALUES('{}','{}','{}')".format(title,body,session['username']))

        #commit to DB

        mysql.connection.commit()

        #close connection

        cur.close()

        flash('Article created','success')

        return redirect(url_for('dashboard'))
    return render_template('add_article.html',form=form)


#edit article

@app.route('/edit_article/<string:id>',methods=['GET','POST'])
@is_logged_in
def edit_article(id):
    #create cursor

    cur=mysql.connection.cursor()

    # get the article by  id

    result=cur.execute("select * from articles where id='{}'".format(id))

    article=cur.fetchone()

    # get form
    form=ArticleForm(request.form)

    #populate article from fields

    form.title.data=article['title']
    form.body.data=article['body']





    if request.method=='POST' and form.validate():
        title=request.form['title']
        body=request.form['body']


        # create a cursor

        cur=mysql.connection.cursor()

        cur.execute("UPDATE articles SET title='{}', body='{}' WHERE id='{}'".format(title,body,id))

        #commit to DB

        mysql.connection.commit()

        #close connection

        cur.close()

        flash('Article Updated','success')

        return redirect(url_for('dashboard'))
    return render_template('edit_article.html',form=form)





# logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('you are now logged out','success')
    return redirect(url_for('login'))


@app.route('/delete_article/<string:id>',methods=['POST'])
@is_logged_in
def delete_article(id):
    #create a cursor
    cur=mysql.connection.cursor()

    cur.execute("DELETE FROM articles WHERE id='{}'".format(id))

    mysql.connection.commit()

    cur.close()

    flash('article deleted','success')
    return redirect(url_for('dashboard'))


if __name__=='__main__':
    app.secret_key='secret123'
    app.run(debug=True)
