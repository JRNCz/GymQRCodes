from flask import Flask, jsonify
from flask import request
from flask import abort
import string
import random
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from flask import jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import sessionmaker
from os import error


app = Flask(__name__)

#SLQ access layer initialization
DATABASE_FILE = "UserData.sqlite"
db_exists = False

engine = create_engine('sqlite:///%s?check_same_thread=False'%(DATABASE_FILE), echo=False) #echo = True shows all SQL calls
Base = declarative_base()

Session = sessionmaker(bind=engine)
session = Session()

class User(Base):
    __tablename__ = 'user'
    user_id = Column(Integer, primary_key=True)
    user_name = Column(String)
    user_secret = Column(String)
    ist_id = Column(String)
    token = Column(String(1000))
    def __repr__(self):
        return (
            self.user_id,
            self.user_name,
            self.user_secret,
            self.ist_id,
            self.token
        )
    def todic2(self):
        return {
            "user_id": self.user_id,
            "user_name": self.user_name,
            "user_secret": self.user_secret,
            "ist_id": self.ist_id,
            "token" : self.token
        }

#Declaration of data
class UserStats(Base):
    __tablename__ = 'userstats'
    stat_id = Column(Integer, primary_key=True)
    date = Column(String)
    gate_id = Column(String)
    ist_id = Column(String, ForeignKey('user.ist_id'))
    user = relationship("User", back_populates="userstats")

    def __repr__(self):
        return (
            self.stat_id,
            self.date,
            self.gate_id,
            self.ist_id
        )
    def todic(self):
        return {
            "stat_id": self.stat_id,
            "date": self.date,
            "gate_id": self.gate_id,
            "ist_id" : self.ist_id
        }
User.userstats =relationship("UserStats",order_by=UserStats.date, back_populates="user")

Base.metadata.create_all(engine) #Create tables for the data models

def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))




#######################################################################
# Atualiza ou Verifica um código de um User
# Input no POST : ISTID
# Output no POST : Atualiza a DB com o novo user secret!
# Input no GET : ISTID
# Output no POST : Retorna um json com "user_secret de um determinado utilizador"
####################################################################################
@app.route("/users/code", methods=['GET', 'POST']) 
def UserGateCode():


    if request.method == 'POST' :

       if ((isinstance(request.json['ist_id'], str)) and ((' ' in request.json['ist_id']) == False)) :

        search_ist_id = request.json['ist_id']

        query = session.query(User).filter(User.ist_id == search_ist_id).first()
        
        newusersecret= id_generator()

        try:
            query.user_secret = newusersecret
            session.commit()
        except:
            print('No user or column allocated to generate a code from - 404 NOT FOUND')
            session.rollback()

        tojson={ "user_secret" : newusersecret }
        return jsonify(tojson)
       else :
           print(' Bad Request on POST /users/code')
           abort(400) 
           




    if request.method == 'GET' :    
     if ((isinstance(request.json['ist_id'], str)) and ((' ' in request.json['ist_id']) == False)) :
        search_ist_id = request.json['ist_id']
        query = session.query(User).filter(User.ist_id == search_ist_id).first()

        user_secret = query.user_secret
        user_token = query.token
        tojson={ "user_secret" : user_secret ,
                 "token" : user_token }
        return jsonify(tojson)
    else :
        print(' Bad Request on GET /users/code')
        abort(400)

#################################################################################
# Atualiza ou Verifica se existe um código de acordo com o INPUT na base de dados
# Input no GER : code
# Output no POST : 1 e userID correspondente ao código ou -1 e userID None ,
####################################################################################

@app.route("/users/checkcode", methods=['GET']) 

def UserCheckCode():

 if ((len(request.json['code']) == 6) and ((' ' in request.json['code']) == False )) : 
     
    query = session.query(User).filter(User.user_secret == request.json['code']).first()
    try :
        personname=query.user_name
        print(personname)
        personid=query.ist_id 
        print(personid)
    except :
        print("Nenhum user tem o código")
        tojson={ "code" : -1 ,
                 "id" : personid }
        return jsonify(tojson)

    tojson={ "code" : 1 ,"id" : personid }
    return jsonify(tojson)
 else: 
     print('User Code is in the wrong format')
     abort(400)

    

#######################################################################
# Stats de um user
# POST - Adiciona um novo stat ao usertendo em conta os inputs IST ID , DATA e GATEID
# O Stat é criado sempre que o user entra numa gate
#########################################################################

@app.route("/user/<id>/stats", methods=['GET', 'POST'])
def UserStatsCode(id):
    
    if request.method == 'POST':
     if ((isinstance(request.json['ist_id'], str) and isinstance(request.json['date'], str) and isinstance(request.json['gate_id'], str) and ((' ' in request.json['ist_id']) == False)) ):

        # Têm json de entrada mas não vão ser verificados erros neste endpoint
        new_ist_id = request.json['ist_id']
        new_date = request.json['date']
        new_gate_id = request.json['gate_id']

        userstats_info = UserStats(date = new_date, gate_id = new_gate_id, ist_id = new_ist_id)
        session.add(userstats_info)
        try:
            session.commit()
        except:
            session.rollback()
        tojson={'post' : 'File created successfully'}
        return jsonify(tojson) 
     else :
         print(' Bad Request User/id/stats')
         abort(400)

    if request.method == 'GET':
        # Não tem Json de entrada 
        query = session.query(UserStats).filter(UserStats.ist_id == id)
        listUserStats = query.all()
        tojson = []
        for f in listUserStats:
                tojson.append(f.todic())
        return jsonify(tojson)


#######################################################################
# Stats de um user
# Verifica se  um determinado user existe na DB.
#########################################################################


@app.route("/oneuser", methods=['GET'])
def OneUser():

    searched_user_name = request.json['user_name']
    searched_ist_id = request.json['ist_id']
    newtoken=request.json['token']


    if request.method == 'GET':
        # Não tem Json de entrada 
        
        try:
            query=session.query(User).filter(User.user_name == searched_user_name, User.ist_id == searched_ist_id).first()
            found_user_id = query.user_id
            tojson={ "user_id" : found_user_id }
            query.token= request.json['token']
            session.commit()

        except:
            tojson={ "user_id" : -1 }
    
        
        return jsonify(tojson)

    return error





#Esta função é agora inutil uma vez que o user cria-se automaticamente sempre que um novo 
#user autentica-se na nossa aplicação!
#Pode ser util que quisermos dar esta opção ao admin

@app.route("/users", methods=['GET','POST'])
def Users():


    if request.method == 'POST':
        # Têm json de entrada mas não vão ser verificados erros neste endpoint
       if ((isinstance(request.json['user_name'], str) and isinstance(request.json['ist_id'], str) and isinstance(request.json['token'], str) and ((' ' in request.json['ist_id']) == False)) ):
        new_user_name = request.json['user_name']
        new_ist_id = request.json['ist_id']
        new_token = request.json['token']
        user_info = User(user_name = new_user_name, user_secret = id_generator(), ist_id = new_ist_id , token = new_token)
        session.add(user_info)
        try:
            session.commit()
        except:
            session.rollback()
        tojson={'post' : 'File created successfully'}
        return jsonify(tojson) 
       else :
           print(' Bad request /users')
           abort(400)

    if request.method == 'GET':
        # Não tem Json de entrada 
        query = session.query(User)
        listUsers = query.all()
        tojson = []
        for f in listUsers:
                tojson.append(f.todic2())

        return jsonify(tojson)

    return error


##############

if __name__ == "__main__":
        app.run(host='0.0.0.0', port=6000, debug=True)