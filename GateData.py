from flask import Flask,jsonify
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
DATABASE_FILE = "GateData.sqlite"
db_exists = False

engine = create_engine('sqlite:///%s?check_same_thread=False'%(DATABASE_FILE), echo=False) #echo = True shows all SQL calls
Base = declarative_base()

Session = sessionmaker(bind=engine)
session = Session()



#Declaration of data
class Gate(Base):
    __tablename__ = 'gate'
    gate_id = Column(Integer, primary_key=True)
    gate_location = Column(String)
    gate_secret = Column(String)
    gate_numb_of_activation = Column(Integer)
    def __repr__(self):
        return (
            self.gate_id,
            self.gate_location,
            self.gate_secret,
            self.gate_numb_of_activation
        )
    def todic(self):
        return {
            "gate_id": self.gate_id,
            "gate_location": self.gate_location,
            "gate_secret": self.gate_secret,
            "gate_numb_of_activation": self.gate_numb_of_activation
        }

#Declaration of data
class GateStats(Base):
    __tablename__ = 'gatestats'
    stat_id = Column(Integer, primary_key=True)
    status = Column(String)
    date = Column(String)
    gate_id = Column(Integer, ForeignKey('gate.gate_id'))
    gate = relationship("Gate", back_populates="gatestats")
    def __repr__(self):
        return (
            self.stat_id,
            self.status,
            self.date,
            self.gate_id
        )
    def todic(self):
        return {
            "stat_id": self.stat_id,
            "status": self.status,
            "date": self.date,
            "gate_id": self.gate_id
        }
Gate.gatestats =relationship("GateStats",order_by=GateStats.date, back_populates="gate")


Base.metadata.create_all(engine) #Create tables for the data models

def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))




############################################################################

@app.route("/gates/code", methods=['GET'])
def GateCode():

 if request.method == 'GET':
     # têm Json de entrada 
     # Confirmar se json vem com um id e é em int ou str
    if ((isinstance(request.json['id'], int) or isinstance(request.json['id'], str)) and ((' ' in request.json['id']) == False)) :   

        id = request.json['id']
        

        try:
            query=session.query(Gate).filter(Gate.gate_id == id).first()
            db_secret = query.gate_secret
        except:
            abort(404)
    
        tojson={ "gate_secret" : db_secret }
        return jsonify(tojson)
    else :
        print('Erro 400 no Gate Code - Formato errado')
        abort(400)


##############
#  Adiciona mais um numb (mais um inicio de sessão) na gate id
############
@app.route("/gates/<id>/numb", methods=['PUT'])
def IncrementNumb (id): 
    
    if request.method == 'PUT':
        # Não têm Json de entrada 

        queryGate=session.query(Gate).filter(Gate.gate_id == id).first()
        gate_numb_of_activation = queryGate.gate_numb_of_activation
        new_gate_numb_of_activation = gate_numb_of_activation + 1

        queryGate.gate_numb_of_activation= new_gate_numb_of_activation
        try:
            session.commit()
        except:
            session.rollback()

        return "numb +1"

##############
# Autoexplicativo 
############
@app.route("/gatestats", methods=['GET', 'POST', 'DELETE'])
def IncrementNumbStats (): 
    
    if request.method == 'POST':


     if ((isinstance(request.json['status'], int) and isinstance(request.json['date'], str) and isinstance(request.json['gate_id'], str)) ):  
        #têm Json de entrada 

        if request.json['status'] == 1:
            get_status = 'Success'
        else:
            get_status = 'Failed'
        get_date = request.json['date']
        get_gate_id = request.json['gate_id']

        gatestats_info = GateStats(status = get_status, date = get_date, gate_id = get_gate_id)
        session.add(gatestats_info)
        try:
            session.commit()
        except:
            print('rollback')
            session.rollback()

        return "numb +1"
     else :
        print('Bad Request gatestats')
        abort(400)

    if request.method == 'GET' : #listgatestats
        # Não tem json de entrada
        try:
            query = session.query(GateStats)
            listGateStats = query.all()
        except:
            abort(404)

        if listGateStats == '':
            return 'No stats'

        tojson = []
        for f in listGateStats:
                tojson.append(f.todic())
        return jsonify(tojson)

################
# Auto-Explicativo
##############
@app.route("/gates", methods=['GET','POST'])
def Gates():

  
    if request.method == 'POST':
        #tem Json de entrada 
     if((isinstance(request.json['gate_location'], str)) and (isinstance(request.json['gate_secret'], str)) and ((' ' in request.json['gate_secret']) == False)) :
         # Ver se a localização e o segrado são uma string e analisar se há espaços no gate secret
        new_gate_location = request.json['gate_location']
        new_gate_secret = request.json['gate_secret']
        gate_info = Gate(gate_location = new_gate_location, gate_secret = new_gate_secret, gate_numb_of_activation = 0)
        session.add(gate_info)
        try:
            session.commit()
        except:
            session.rollback()

        tojson={'post' : 'File created successfully'}
        return jsonify(tojson) 
     else :
        abort(400)
    
    if request.method == 'GET': #listgate
        # Não tem json de entrada

        try:
            query = session.query(Gate)
            listGates = query.all()
        except:
            abort(404)

        tojson = []
        for f in listGates:
                tojson.append(f.todic())
        return jsonify(tojson)

    return error

if __name__ == "__main__":
        app.run(host='0.0.0.0', port=7000, debug=True)