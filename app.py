from flask import Flask, redirect, url_for, render_template, request, session, flash, make_response
import requests
import os
import dotenv
from dotenv import load_dotenv, find_dotenv
import pymongo
from pymongo import MongoClient
import random
import datetime

app = Flask(__name__)
app.secret_key = os.getenv('APP_SECRET')

find_dotenv()
load_dotenv()

cluster = MongoClient(os.getenv('MONGO_URL'))
db = cluster['Personal']
users_collection = db['NexTech']


@app.route('/', methods = ['GET'])
def landing():
    if request.method == 'GET':
        return render_template('landing.html')


@app.route('/signup', methods = ['GET', 'POST'])
def signup():
    if 'email' not in session:
        if request.method == 'GET':
            return render_template('register.html')

        elif request.method == 'POST':
            email = request.form.get('Email')
            password = request.form.get('Password')
            confirm_password = request.form.get('PasswordConfirm')
            name = request.form.get('Name')
            
            print(password)

            if str(password) == str(confirm_password):

                try:

                    account_exists = users_collection.find_one({'Email': email})
                    password_exists = account_exists['Password']
                
                    flash('You already have an account!')
                    return render_template('register.html')
                except:

                    post = {'Email': email.lower(), 'Password': password, 'Type': 'Teacher', 'Name': name}
                    users_collection.insert_one(post)
                    return redirect(url_for('teacherProfile'))
                    session['email'] = email
                    email = email.lower()
                    session['password'] = password
                    

            else:
                flash('Your passwords do not match!')
                return render_template('register.html')

    else:
        if session['type'] == 'Student':
            return redirect(url_for('studentProfile'))

        else:
            return redirect(url_for('teacherProfile'))


@app.route('/signin', methods = ['GET', 'POST'])
def signin():
    if 'email' not in session:
        if request.method == 'GET':
            return render_template('signin.html')
            
        elif request.method == 'POST':
            email = request.form.get('Email').lower()
            password = request.form.get('Password')

            try:

                account_exists = users_collection.find_one({'Email': email, 'Password': password})
                session['email'] = account_exists['Email']
                session['password'] = account_exists['Password']
                session['type'] = account_exists['Type']
                if str(session['type']) == 'Student':
                    return redirect(url_for('studentProfile')) 
                


            except:
                flash('Incorrect Username/Password!')
                return render_template('signin.html')
            
            return redirect(url_for('teacherProfile'))
    else:
        if session['type'] == 'Student':
            return redirect(url_for('studentProfile'))

        else:
            return redirect(url_for('teacherProfile'))


@app.route('/teacherprofile', methods = ['GET', 'POST'])
def teacherProfile():
    if 'email' in session:
        if request.method == 'GET':
            teacher_account = users_collection.find_one({'Email': session['email']})
            name = teacher_account['Name']
            session['name'] = name

            tests_names = []
            tests_percentages = []
            tests_dates = []

            current_date = datetime.datetime.today().strftime ('%m/%d/%Y')
            tests_taken = users_collection.find({'Type': 'Answers', 'Date': current_date,  'Teacher': str(session['name'])})

            for test in tests_taken:
                tests_names.append(test['Name'])
                tests_dates.append(test['Date'])
                tests_percentages.append(test['Percentage'])

            count = len(tests_names)

            return render_template('teacherprofile.html', name=name, type=session['type'], count= count, names=tests_names, percentages=tests_percentages, dates = tests_dates)



        elif request.method == 'POST':
            pass
    else:
        return redirect(url_for('signin'))


@app.route('/studentprofile', methods = ['GET', 'POST'])
def studentProfile():
    if 'email' in session:
        if request.method == 'GET':
            student_account = users_collection.find_one({'Email': session['email']})
            student_name = student_account['Name']
            teacher_name = student_account['Teacher']
            session['name'] = student_name
            session['teacher'] = teacher_name

            last_date = users_collection.find_one({'Email': session['email'], 'Type': 'LastDate'})


            return render_template('studentprofile.html', name=student_name, teacher_name = teacher_name, last_date = last_date['Date'])

        elif request.method == 'POST':
            pass
    else:
        return redirect(url_for('signin'))


@app.route('/teacherprofile/userslist', methods=['GET', 'POST'])
def usersList():
    if request.method == 'GET':
        if 'email' in session and session['type'] == 'Teacher':
            student_list = users_collection.find({'Type': 'Student', 'Teacher': session['name']})
            student_names = []
            student_emails = []
            for student in student_list:
                student_names.append(student['Name'])
                student_emails.append(student['Email'])

            lencount = len(student_emails)
            count = range(0, lencount)


            return render_template('userslist.html', count = len(student_emails), emails=student_emails, names=student_names)

    else:
        return redirect(url_for('logout'))


@app.route('/teacherprofile/userslist/<email>', methods=['GET', 'POST'])
def usersEdit(email):
    if 'email' in session and session['type'] == 'Teacher':
        if request.method == 'GET':
            student_account = users_collection.find_one({'Email': email, 'Type': 'Student'})
            student_name = student_account['Name']

            return render_template('usersedit.html', email=email, name = student_name)
        if request.method == 'POST':
            edited_name = request.form.get('name')
            edited_email = request.form.get('email').lower()

            if len(edited_name) > 0 and len(edited_email) > 0:
                old_account = users_collection.find_one({'Email': email, 'Type': 'Student'})
                old_name = old_account['Name']
                print(old_name)

                users_collection.find_one_and_update({'Email': email, 'Type': 'Student'}, {'$set' :{'Email': edited_email, 'Name': edited_name}})

                
                users_collection.update_many({'Name': str(old_name), 'Type': 'Answers'}, {'$set':{'Name': edited_name}})

                flash('Student Updated!')
                return redirect(url_for('usersList'))
            else:
                flash('Please fill out both fields!')
                student_account = users_collection.find_one({'Email': email, 'Type': 'Student'})
                student_name = student_account['Name']

                return render_template('usersedit.html', email=email, name = student_name)
    else:
        return redirect(url_for('logout'))                



@app.route('/teacherprofile/userslist/newuser', methods=['GET', 'POST'])
def newUser():
    if 'email' in session and session['type'] == 'Teacher':
        if request.method == 'GET':
            return render_template('newuser.html')

        if request.method == 'POST':
            email = request.form.get('email')
            name = request.form.get('name')
            password = request.form.get('password')
            print(email, 'EMAIL')
            print(name, 'NAME')
            print(password, 'PASSWORD')

            if len(email) > 0 and len(name) > 0 and len(password) > 0 :

                post = {'Email': email.lower(), 'Password': password, 'Type': 'Student', 'Name': name, 'Teacher': session['name']}
                users_collection.insert_one(post)

                post = {'Email': email.lower(), 'Type': 'LastDate', 'Name': name, 'Date': 'Never'}
                users_collection.insert_one(post)
                

                flash('Student Successfully Created!')
                return redirect(url_for('usersList'))

            else:
                flash('Please fill out all fields!')
                return render_template('newuser.html')

    else:
        return redirect(url_for('logout'))                


@app.route('/teacherprofile/userslist/deluser/<email>')
def delUser(email):
    if 'email' in session and session['type'] == 'Teacher':
        old_account = users_collection.find_one({'Email': email})
        name = old_account['Name']
        users_collection.remove({'Email': email})

        users_collection.delete_many({'Name': name, 'Teacher': session['name'], 'Type': 'Answers'})

        flash('Student successfully deleted!')
        return redirect(url_for('usersList'))
    else:
        return redirect(url_for('logout'))


question = ''
@app.route('/studentprofile/question/<question_number>', methods=['GET', 'POST'])
def quiz(question_number):
    if 'email' in session and session['type'] == 'Student':

        global question
        if request.method == 'GET':
            
            questions_full_list =  users_collection.find_one({'Type': 'Questions'})
            question_index = str('Question' + question_number)
            questions_list = questions_full_list[question_index]
            question = random.choice(questions_list)
            question_number_title = f'Question #{int(question_number)}'

            return render_template('question.html', question=question, question_title= question_number_title)

        elif request.method == 'POST':
            
            question = question
            answer_choice = request.form.get('response')

            if answer_choice is None:
                flash('Please choose an answer!')
                return redirect(f'/studentprofile/question/{question_number}')

            question_number = int(question_number)
            current_date = datetime.datetime.today().strftime ('%m/%d/%Y')

    

            if question_number == 1:
                users_collection.remove({'Date': current_date, 'Name': session['name'], 'Type': 'Answers'})

                post = {'Type': 'Answers', 'Name': session['name'], 'Questions': [question], 'Answers': [answer_choice], 'Date': current_date, 'Teacher': str(session['teacher'])}
                users_collection.insert_one(post)

            elif question_number == 5:
                student_answers = users_collection.find_one({'Type': 'Answers', 'Name': session['name'], 'Date': current_date})
                previous_questions = student_answers['Questions']
                previous_answers = student_answers['Answers']

                users_collection.find_one_and_update({'Email': session['email'], 'Type': 'LastDate'}, {'$set' :{'Date': current_date}})

                previous_questions.append(question)
                previous_answers.append(answer_choice)
       
                total_points = 0
                for choice in previous_answers:
                    total_points += int(choice)

                    percentage = total_points / 20
                    percentage = percentage * 100

                    percentage = round(percentage)

                users_collection.find_one_and_update({'Type': 'Answers', 'Name': session['name'], 'Date': current_date}, {'$set' :{'Questions': previous_questions, 'Answers': previous_answers, 'Percentage': percentage}})

                flash('Test submitted!')
                return redirect(url_for('studentProfile'))            
            
            else:
                student_answers = users_collection.find_one({'Type': 'Answers', 'Name': session['name'], 'Date': current_date})
                previous_questions = student_answers['Questions']
                previous_answers = student_answers['Answers']

                previous_questions.append(question)
                previous_answers.append(answer_choice)



                users_collection.find_one_and_update({'Type': 'Answers', 'Name': session['name'], 'Date': current_date}, {'$set' :{'Questions': previous_questions, 'Answers': previous_answers}})



            question_number += 1
            return redirect(f'/studentprofile/question/{question_number}')

    else:
        return redirect(url_for('logout'))            


@app.route('/teacherprofile/export/<email>', methods=['GET'])
def exportList(email):
    if 'email' in session and session['type'] == 'Teacher':
        if request.method == 'GET':
            student = users_collection.find_one({'Type': 'Student', 'Email': email, 'Teacher': session['name']})

            student_name = student['Name']
            current_date = datetime.datetime.today().strftime ('%m/%d/%Y')

            student_answers = users_collection.find({'Type': 'Answers', 'Name': student_name})

            dates = []
            questions = []
            answers = []
            percentages = []
            answers_text = []

            for quiz in student_answers:
                dates.append(quiz['Date'])
                questions = quiz['Questions']
                answers = quiz['Answers']
                percentages.append(quiz['Percentage'])


            for choice in answers:
                if choice == '1':
                    answers_text.append('Not at All')
                elif choice == '2':
                    answers_text.append('Serveral Days')
                elif choice == '3':
                    answers_text.append('More than half the days')
                elif choice == '4':
                    answers_text.append('Nearly Every Day')

            
            count = len(dates)

            return render_template('export.html', name=student_name, current_date=current_date, dates=dates, questions=questions, answers=answers_text, percentages=percentages, count=count)

    else:
        return redirect(url_for('logout'))            

@app.errorhandler(404)
def internal_error(error):

    return '<p> Something goofed! Go back to normal </p> <a href="/signin">here</a>'
    
@app.route('/logout', methods=['POST', 'GET'])
def logout():
    session.pop('email', None)
    session.pop('password', None)
    session.pop('name', None)
    session.pop('type', None)
    session.pop('teacher', None)
    return redirect(url_for('signin'))    


if __name__ == '__main__':
    app.run(host='0.0.0.0', port = 80, debug=True)
