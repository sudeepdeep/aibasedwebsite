from flask import Flask, render_template,url_for, redirect, flash, session
import speech_recognition as sr
import os
import face_recognition
import cv2
import numpy as np
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
from flask import *
from werkzeug.utils import secure_filename
import qrcode
import ast
from pyzbar.pyzbar import decode
import pyttsx3
import pickle as pkl
from translate import Translator



barcode_img = os.path.join('static', 'images')
app = Flask(__name__)
app.secret_key = "hellosudeep"

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'deepu'
app.config['MYSQL_PASSWORD'] = '12345'
app.config['MYSQL_DB'] = 'userregistration'

mysql = MySQL(app)


app.config['UPLOAD_FOLDER'] = barcode_img

@app.route("/")
def home():
    if 'loggedin' in session:
        return render_template('home.html',log = 'logout')
    else:
        return render_template('home.html',log = 'login')
@app.route("/login",methods = ['POST','GET'])
def login():
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM register WHERE email = %s AND password = %s', (email, password,))
        account = cursor.fetchone()
        if account:
            session['loggedin'] = True
            session['email'] = email
            return redirect(url_for('home'))
        else:
            flash('Credentials incorrect!!')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    # Remove session data, this will log the user out
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('email', None)
   return redirect(url_for('login'))
@app.route("/register",methods = ["POST","GET"])
def register():
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'repassword' in request.form and 'email' in request.form:
        username = request.form['username']
        password = request.form['password']
        repassword = request.form['repassword']
        email = request.form['email']

        if password == repassword:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM  register WHERE email = %s',[email])
            account = cursor.fetchone()
            if account:
                flash('Email alreay taken!!')
                return redirect(url_for('register'))
            elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
                flash('Invaid email address')
                return redirect(url_for('register'))
            elif not re.match(r'[A-Za-z0-9]+', username):
                flash('Username must contain only characters and numbers!')
                return redirect(url_for('register'))

            else:
                cursor.execute('INSERT INTO register VALUES (NULL, %s, %s, %s)', (username, email, password,))
                mysql.connection.commit()
                qrname = username
                qremail = email
                data = {'name':qrname,'email':qremail}
                qr = qrcode.QRCode(version = 5,box_size = 5,border = 1)
                qr.add_data(data)
                qr.make(fit = True)
                path = "C:/Users/dell/Desktop/flask/static/images"
                img = qr.make_image(fill_color = 'black',back_color = 'white')
                img.save(f"{path}/{qrname}.png")
                flash('Registration successful')
                return redirect(url_for('login'))
    elif request.method == 'POST':
        flash('Please fill the form')
        return redirect(url_for('register'))
    return render_template('register.html')


@app.route("/profile")
def profile():  
    if  "email" in session:
        profileemail = session['email']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM register WHERE email = %s',(profileemail,))
        account = cursor.fetchone()
        qrnamee = f"{account['name']}.png"
        full_filename = os.path.join(app.config['UPLOAD_FOLDER'], f'{qrnamee}')
        return render_template('profile.html', account=account,user_image = full_filename)
    elif "barmail" in session:
        profileemail = session['barmail']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM register WHERE email = %s',(profileemail,))
        account = cursor.fetchone()
        qrnamee = f"{account['name']}.png"
        full_filename = os.path.join(app.config['UPLOAD_FOLDER'], f'{qrnamee}')
        return render_template('profile.html', account=account,user_image = full_filename)



    else:
        return redirect(url_for('login'))

@app.route('/barcodelogin')
def barcodelogin():
    cap = cv2.VideoCapture(0)
    while True:
        ret,frame = cap.read()
        for barcode in decode(frame):
            data = barcode.data.decode('ascii')
            info = ast.literal_eval(data)
            barmail = info['email']
            #new_data = re.split(':|,',data)
            #barmail = new_data[3][1:-1]
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM register WHERE email = %s',(barmail,))
            account = cursor.fetchone()
            if account:
                session['loggedin'] = True
                session['email'] = barmail
                return redirect(url_for('home'))
            else:
                return render_template('login.html')
        cv2.imshow("frame",frame)
        if cv2.waitKey(1) == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()
    return render_template('barcodelogin.html')


@app.route("/tts",methods = ["POST","GET"])
def tts():
    if 'loggedin'  in session:
        if request.method == "POST" and 'nm' in request.form:
            mytext = str(request.form['nm'])
            engine = pyttsx3.init()
            engine.say(mytext)
            engine.runAndWait()
            return redirect(url_for('tts'))

        
    else:
        return redirect(url_for('login'))
    return render_template('tts.html')

@app.route("/stt",methods = ["POST","GET"])
def stt():
    if 'loggedin'  in session:
        if request.method == "POST":
            r = sr.Recognizer()
            with sr.Microphone() as source:

                r.adjust_for_ambient_noise(source)
                audio = r.listen(source)
                text = r.recognize_google(audio)
            
                return redirect(url_for('stt_speak',txt = text))

        
    else:
        return redirect(url_for('login'))

    return render_template('stt.html')
@app.route("/stt/<txt>")
def stt_speak(txt):
    return f"<h1>you said {txt}</h1>"


@app.route('/selectfile')
def selectfile():
    if 'loggedin' in session:
        return render_template('selectfile.html')
    else:
        return redirect(url_for('login'))

@app.route('/uploadfile',methods = ['POST','GET'])
def uploadfile():
    if request.method == "POST":
        cap = cv2.VideoCapture(0)
        uname = request.form['uname']
        f = request.files['file']
        f.save(secure_filename(f.filename))
        name = f.filename
        usr_image = face_recognition.load_image_file(f'{name}')
        usr_encoding = face_recognition.face_encodings(usr_image)[0]
        known_face_encodings = [usr_encoding]
        known_face_name = [f'{uname}']
        face_locations = []

        face_encodings = []

        face_names = []

        process_this_frame = True

        while True:

            ret,frame = cap.read()

            small_frame = cv2.resize(frame,(0,0),fx = 0.25,fy = 0.25)

            rgb_frame = small_frame[:,:,::-1]

            if process_this_frame:

                face_locations = face_recognition.face_locations(rgb_frame)

                face_encodings = face_recognition.face_encodings(rgb_frame,face_locations)

                face_names = []

                for face_encoding in face_encodings:

                    matches = face_recognition.compare_faces(known_face_encodings,face_encoding)

                    name ='unknown'

                    face_distances = face_recognition.face_distance(known_face_encodings,face_encoding)
                    best_match_index = np.argmin(face_distances)

                    #print(best_match_index)

                    if matches[best_match_index]:
                        name = known_face_name[best_match_index]

                        face_names.append(name)

            process_this_frame = not process_this_frame

            for (top,right,bottom,left),name in zip(face_locations,face_names):

                top*=4
                right*=4
                bottom*=4
                left*=4

                cv2.rectangle(frame,(left,top),(right,bottom),(255,0,0),2)

                cv2.rectangle(frame,(left,bottom-35),(right,bottom),(255,0,0),cv2.FILLED)

                cv2.putText(frame,name,(left+5,bottom - 6),cv2.FONT_HERSHEY_DUPLEX,1,(255,255,255),1)

            cv2.imshow('frame',frame)

            if cv2.waitKey(1) &0xFF == ord('q'):
                break

        cap.release()

        cv2.destroyAllWindows()

    return render_template('selectfile.html')


@app.route('/newfeatures')
def newfeatures():
    if 'loggedin' in session:
        return render_template('newfeatures.html')
    return redirect(url_for('login'))  



@app.route('/facerecognize',methods = ['POST','GET'])
def facerecognize():
    '''
    if request.method == "POST":
        facename = request.form['userface']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM  facerecognition WHERE facename = %s',[facename])
        account = cursor.fetchone()
        if account:
            flash('name alreay taken!!')
            return redirect(url_for('facerecognize'))
        else:
            t = (facename,)
            cursor.execute('INSERT INTO facerecognition VALUES (NULL, %s)', t)
            mysql.connection.commit()
            f = request.files['file']
            f.save(secure_filename(f.filename))
            name = f.filename
            usr_image = face_recognition.load_image_file(f'{name}')
            usr_encoding = face_recognition.face_encodings(usr_image)[0]
            known_face_encodings = [usr_encoding]
            known_face_name = [f'{facename}']
            return redirect(url_for('facelogin',knownencodings = known_face_encodings,knownname = known_face_name))
            '''
    return render_template('facerecognize.html')

@app.route('/facelogin')
def facelogin():
    '''
    cap = cv2.VideoCapture(0)
    face_locations = []

    face_encodings = []

    face_names = []

    process_this_frame = True

    while True:
        ret,frame = cap.read()

        small_frame = cv2.resize(frame,(0,0),fx = 0.25,fy = 0.25)

        rgb_frame = small_frame[:,:,::-1]

        if process_this_frame:

            face_locations = face_recognition.face_locations(rgb_frame)

            face_encodings = face_recognition.face_encodings(rgb_frame,face_locations)

            face_names = []

            for face_encoding in face_encodings:

                matches = face_recognition.compare_faces(knownencodings,face_encoding)

                name ='unknown'

                face_distances = face_recognition.face_distance(knownencodings,face_encoding)
                best_match_index = np.argmin(face_distances)

                #print(best_match_index)

                if matches[best_match_index]:
                    name = knownname[best_match_index]

                    face_names.append(name)
                    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                    cursor.execute('SELECT * FROM facerecognition WHERE facename = %s', (name))
                    account = cursor.fetchone()
                    if account:
                        session['loggedin'] = True
                        return redirect(url_for('home'))
                    else:
                        flash('Face Not Recognized properly')
                        return render_template('facelogin.html')

        process_this_frame = not process_this_frame
        cv2.imshow('frame',frame)

        if cv2.waitKey(1) &0xFF == ord('q'):
            break

    cap.release()

    cv2.destroyAllWindows()

    '''

    return render_template('facelogin.html')
'''
@app.route('/audiobook',methods = ['GET','POST'])
def audiobook():
    if request.method == "POST":
        f = request.files['file']
        f.save(secure_filename(f.filename))
        name = f.filename
        book = open(f'{name}','rb')
        pdfReader = PyPDF2.PdfFileReader(book)
        for page_num in range(pdfReader.numPages):
            text =  pdfReader.getPage(page_num).extractText()
            language = "en"
            op = gTTS(text = text, lang = language, slow = False)
            op.save("op.mp3")
            os.system("start op.mp3")
            


    return render_template('audiobook.html')
'''
@app.route('/ipl')
def ipl():
    if 'loggedin' in session:
        return render_template('ipl.html')

@app.route('/iplpredictions',methods = ['GET','POST'])
def iplpredictions():
    if 'loggedin' in session:
        team1 = str(request.args.get('list1'))
        team2 = str(request.args.get('list2'))

        toss_win  = int(request.args.get('toss_winner'))
        choose = int(request.args.get('fb'))

        


       
        with open(r'C:\Users\dell\Desktop\flask\app\inv_vocab.pkl', 'rb') as f:
            inv_vocab = pkl.load(f)

        with open(r'C:\Users\dell\Desktop\flask\app\model.pkl', 'rb') as f:
            model = pkl.load(f)

        cteam1 = inv_vocab[team1]
        cteam2 = inv_vocab[team2]

        if cteam1 == cteam2:
            data  = "Please select different teams"
            return render_template('error.html',data  = data)

        lst = np.array([cteam1, cteam2, choose, toss_win], dtype='int32').reshape(1,-1)
        prediction = model.predict(lst)
        if prediction == 0:
            team_win = team1
            teamname = f"{team1}.jpg"
        else:
            team_win = team2
            teamname = f"{team2}.jpg"
        full_filename = os.path.join(app.config['UPLOAD_FOLDER'], f'{teamname}')
        return render_template('res.html', data  = team_win, teampath = full_filename)
    else:

        return render_template('login.html')
    return render_template('ipl.html')


@app.route('/paidfeatures')
def paidfeatures():
    return render_template('paidfeatures.html')

@app.route('/languagetranslator',methods = ['POST','GET'])
def languagetranslator():
    if 'loggedin' in session:
        if request.method == "POST":
            lang1 = str(request.form['src'])
            lang2 = str(request.form['dest'])
            text = str(request.form['lang'])
            translator= Translator(from_lang = f'{lang1}',to_lang=f'{lang2}')
            translation = translator.translate(f'{text}')

            return render_template('translator.html',text = translation)
    else:
        return redirect(url_for('login'))

    return render_template('languagetranslator.html')


if __name__ == "__main__":
	app.run(debug = True)
