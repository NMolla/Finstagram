# Import Flask Library
from flask import Flask, render_template, request, session, url_for, redirect
import pymysql.cursors
from hashlib import sha256
SALT = 'cs3083'
# Initialize the app from Flask
app = Flask(__name__)

# Configure MySQL
conn = pymysql.connect(host='localhost',
                       port=3306,
                       user='root',
                       password='root', #set password accordingly
                       db='finstagram',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)


# Define a route to hello function
@app.route('/')
def hello():
    return render_template('index.html')


# Define route for login
@app.route('/login')
def login():
    return render_template('login.html')


# Define route for register
@app.route('/register')
def register():
    return render_template('register.html')


# Authenticates the login
@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
    # grabs information from the forms
    username = request.form['username']
    password = request.form['password']

    hashed_password = sha256((password + SALT).encode('utf-8')).hexdigest()
    # cursor used to send queries
    cursor = conn.cursor()
    # executes query
    query = 'SELECT * FROM person WHERE username = %s and password = %s'
    cursor.execute(query, (username, hashed_password))
    # stores the results in a variable
    data = cursor.fetchone()
    # use fetchall() if you are expecting more than 1 data row
    cursor.close()
    error = None
    if (data):
        # creates a session for the the user
        # session is a built in
        session['username'] = username
        return redirect(url_for('home'))
    else:
        # returns an error message to the html page
        error = 'Invalid login or username'
        return render_template('login.html', error=error)


# Authenticates the register
@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():
    # grabs information from the forms
    username = request.form['username']
    password = request.form['password']
    firstName = request.form['firstName']
    lastName = request.form['lastName']
    bio = request.form['bio']

    hashed_password = sha256((password+SALT).encode('utf-8')).hexdigest()

    # cursor used to send queries
    cursor = conn.cursor()
    # executes query
    query = 'SELECT * FROM person WHERE username = %s'
    cursor.execute(query, (username))
    # stores the results in a variable
    data = cursor.fetchone()
    # use fetchall() if you are expecting more than 1 data row
    error = None
    if (data):
        # If the previous query returns data, then user exists
        error = "This user already exists"
        return render_template('register.html', error=error)
    else:
        ins = 'INSERT INTO person VALUES(%s, %s, %s, %s, %s)'
        cursor.execute(ins, (username, hashed_password, firstName, lastName, bio))
        conn.commit()
        cursor.close()
        return render_template('index.html')


@app.route('/home')
def home():
    user = session['username']
    cursor = conn.cursor();
    query = 'SELECT allPhotos.photoPoster, allPhotos.photoID, allPhotos.caption, allPhotos.postingDate \
            FROM \
            ((SELECT photoPoster, photoID, caption, postingDate \
            FROM Follow AS f JOIN Photo AS p on f.username_followed = p.photoPoster \
            WHERE f.username_follower = %s AND f.followStatus = 1) \
            UNION \
            (SELECT photoPoster, photoID, caption, postingDate \
            FROM (SharedWith AS sw JOIN BelongTo AS bt ON sw.groupOwner = bt.owner_username AND \
            sw.groupName = bt.groupName) NATURAL JOIN photo \
            WHERE member_username = %s)) as allPhotos \
            ORDER BY allPhotos.postingDate DESC'
    query2 = 'SELECT photoPoster, photoID, caption, postingDate \
              FROM photo WHERE photoPoster = %s \
              ORDER BY postingDate DESC'
    query3 = 'SELECT groupName, member_username FROM BelongTo WHERE \
              owner_username=%s AND member_username != %s ORDER BY groupName'
    query4 = 'SELECT owner_username, groupName FROM BelongTo WHERE \
              member_username=%s AND owner_username != %s ORDER BY owner_username'
    cursor.execute(query, (user, user))
    data = cursor.fetchall()
    cursor.execute(query2, (user))
    data2 = cursor.fetchall()
    cursor.execute(query3, (user, user))
    data3 = cursor.fetchall()
    cursor.execute(query4, (user, user))
    data4 = cursor.fetchall()
    cursor.close()
    return render_template('home.html', username=user, photos=data, myphotos=data2, mygroups=data3, ingroups=data4)


@app.route('/post', methods=['GET', 'POST'])
def post():
    photoposter = session['username']
    cursor = conn.cursor();
    filepath = request.form['filepath']
    allFollowers = request.form['allFollowers']
    caption = request.form['caption']
    query = 'INSERT INTO photo (filepath, allFollowers, caption, photoposter) VALUES(%s, %s, %s, %s)'
    cursor.execute(query, (filepath, allFollowers, caption, photoposter))
    conn.commit()
    cursor.close()
    return redirect(url_for('home'))

@app.route('/follow')
def follow():
    follower = session['username']
    cursor = conn.cursor();
    query = 'SELECT DISTINCT username FROM person WHERE username != %s and username NOT IN \
            (SELECT username_followed FROM follow WHERE username_follower = %s)'
    cursor.execute(query, (follower, follower))
    data = cursor.fetchall()
    cursor.close()
    error = None
    if (data):
        return render_template('select_Person_toFollow.html', user_list=data)
    else:
        error = "There are no users for this user to follow"
        return render_template('home.html', error=error)


@app.route('/requestFollow', methods=["GET", "POST"])
def requestFollow():
    username_followed = request.args['username_followed']
    username_follower = session['username']
    cursor = conn.cursor();
    ins = 'INSERT INTO follow VALUES(%s, %s, 0)'
    cursor.execute(ins, (username_followed, username_follower))
    conn.commit()
    cursor.close()
    return redirect(url_for('home'))

@app.route('/seeFollowRequests')
def seeFollowRequests():
    username = session['username']
    cursor = conn.cursor();
    query = 'SELECT DISTINCT username_follower FROM follow WHERE username_followed = %s and followstatus = 0'
    cursor.execute(query, username)
    data = cursor.fetchall()
    cursor.close()
    error = None
    if (data):
        return render_template('selectRequestToAccept.html', user_list=data)
    else:
        error = "There are no follow requests for this user"
        return render_template('home.html', error=error)

@app.route('/acceptFollow', methods=["GET", "POST"])
def acceptFollow():
    follower = request.args['username_follower']
    followed = session['username']
    cursor = conn.cursor();
    upd = 'UPDATE follow SET followstatus = 1 WHERE username_followed = %s AND username_follower = %s'
    cursor.execute(upd, (followed, follower))
    conn.commit()
    cursor.close()
    return redirect(url_for('home'))

@app.route('/createFriendGroup', methods=["GET", "POST"])
def createFriendGroup():
    groupOwner = session['username']
    groupName = request.form['FriendGroupName']
    description = request.form['description']
    cursor = conn.cursor();
    check = 'SELECT * FROM friendgroup WHERE groupOwner = %s and groupName = %s'
    cursor.execute(check, (groupOwner, groupName))
    data = cursor.fetchall()
    error = None
    if (data):
        cursor.close()
        error = "This friendgroup already exists"
        return render_template('home.html', error=error)
    else:
        query = 'INSERT INTO friendgroup VALUES(%s, %s, %s)'
        cursor.execute(query, (groupOwner, groupName, description))
        query2 = 'INSERT INTO belongto VALUES(%s, %s, %s)'
        cursor.execute(query2, (groupOwner, groupOwner, groupName))
        conn.commit()
        cursor.close()
        return redirect(url_for('home'))

@app.route('/addToFriendGroup', methods=["GET", "POST"])
def addToFriendGroup():
    owner_username = session['username']
    groupName = request.form['FriendGroupName']
    member_username = request.form['username']
    cursor = conn.cursor();
    check = 'SELECT * FROM friendgroup WHERE groupOwner = %s and groupName = %s'
    cursor.execute(check, (owner_username, groupName))
    data = cursor.fetchall()
    error = None
    if (data):
        check2 = 'SELECT username FROM person WHERE username = %s'
        cursor.execute(check2, (member_username))
        data = cursor.fetchall()
        if (data):
            check3 = 'SELECT * FROM belongto WHERE owner_username = %s and groupName = %s and member_username = %s'
            cursor.execute(check3, (owner_username, groupName, member_username))
            data = cursor.fetchall()
            if (data):
                cursor.close()
                error = "This person is already in that friend group"
                return render_template('home.html', error=error)
            else:
                query = 'INSERT INTO belongto VALUES(%s, %s, %s)'
                cursor.execute(query, (member_username, owner_username, groupName))
                cursor.close()
                return redirect(url_for('home'))
        else:
            cursor.close()
            error = "This person does not exists"
            return render_template('home.html', error=error)
    else:
        cursor.close()
        error = "This friendgroup does not exists"
        return render_template('home.html', error=error)


@app.route('/logout')
def logout():
    session.pop('username')
    return redirect('/')


app.secret_key = 'some key that you will never guess'
# Run the app on localhost port 5000
# debug = True -> you don't have to restart flask
# for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
    app.run('127.0.0.1', 5001, debug=True)
