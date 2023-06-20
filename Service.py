from flask import Flask, render_template, jsonify
import os
from flask import request
import requests
from flask import abort
from requests_oauthlib import OAuth2Session
import string
import random
from sqlalchemy.ext.declarative import declarative_base
from flask import jsonify
import datetime
from datetime import datetime
from flask import Flask, request, redirect, session, url_for
from flask.json import jsonify
import os
import qrcode
import threading



#CHANGE THE DEFAULT IP FOR THE GATE DATA's IP BEFORE RUNNING
# CHANGE THIS VARIABLES
# CHANGE THE IP IN SCANQR.html (templates) too to the right server adress (A HTML FILE)
ipgatedatareplica = 'http://192.168.1.90:9000'
ipgatedata = 'http://192.168.1.90:7000'
ipuserdata = 'http://192.168.1.90:6000'
redirectURL= 'http://192.168.1.90:8000'
client_id = "570015174623407"
client_secret = "WVlqsPmzNHcjiL9HG5p0UXXKVogDwxzOGqG3Rfd3l4J0cGiDQ1RiuTOmG3TNHG3RzpbXCHEOhh+CQN51gH3dhQ=="
qrcodeurl = "C:/Users/joaor/Desktop/PROJETOV6/static/lastuserQRcode.png"
timer=0


authorization_base_url = 'https://fenix.tecnico.ulisboa.pt/oauth/userdialog'
token_url = 'https://fenix.tecnico.ulisboa.pt/oauth/access_token'

app = Flask(__name__)

def timerfunction(arg):

 try:  
    print ("Tempo do QR Code expirado! - Vai-se atribuir um novo")
    # Não há json de entrada
    user= { 'ist_id' : arg }
    response = requests.post(ipuserdata + '/users/code', json= user)
    print('Sucess')
    return "Sucess"
 except :
     return "Timer Failed"


########### EM DESENVOLVIMENTO ##################
#
#

@app.route("/")
def demo():
    """Step 1: User Authorization.

    Redirect the user/resource owner to the OAuth provider (i.e. Github)
    using an URL with a few key OAuth parameters.
    """
    github = OAuth2Session(client_id, redirect_uri= redirectURL+"/callback")
    authorization_url, state = github.authorization_url(authorization_base_url)
    # State is used to prevent CSRF, keep this for later.
    session['oauth_state'] = state
    return redirect(authorization_url)


# Step 2: User authorization, this happens on the provider.

@app.route("/callback", methods=["GET"])
def callback():
    """ Step 3: Retrieving an access token.

    The user has been redirected back from the provider to your registered
    callback URL. With this redirection comes an authorization code included
    in the redirect URL. We will use that to obtain an access token.
    """

    try:
        github = OAuth2Session(client_id, state=session['oauth_state'], redirect_uri= redirectURL+"/callback")
        token = github.fetch_token(token_url, client_secret=client_secret,
                                authorization_response=request.url)

        # At this point you can fetch protected resources but lets save
        # the token and show how this is done from a persisted token
        # in /profile.
        session['oauth_token'] = token

        #if check user
        return redirect(url_for('.authSucess'))
    except Exception as e :
        print("An error occurred:", e)
        
        


@app.route("/authsucess", methods=["GET"])
def authSucess():
    """Fetching a protected resource using an OAuth 2 token.
    """
    
    github = OAuth2Session(client_id, token=session['oauth_token'])

    print('\n')
    istNumber = github.get('https://fenix.tecnico.ulisboa.pt/api/fenix/v1/person').json()['username']
    user_name = github.get('https://fenix.tecnico.ulisboa.pt/api/fenix/v1/person').json()['displayName']

    session["istNumber"] = istNumber

    tojson={ 
        "user_name" : user_name,
        "ist_id" : istNumber,
        "token" : str(session["oauth_token"])
    }

    # Se for um user que não existe , criar na nossa(s) DBs
    if requests.get(ipuserdata + '/oneuser', json = tojson).json()['user_id'] == -1: 
            requests.post(
                ipuserdata + '/users', 
                json = tojson
        )

    return redirect(url_for('.menu'))





@app.route("/menu")
def menu():
 if(str(session['oauth_token']) == requests.get(ipuserdata + '/users/code', json = { 'ist_id' : session["istNumber"]}).json()['token']) :  
    return render_template(
        'menu.html'
    )
 else : 
        return render_template("invalidtoken.html")
     

##########
# Renderiza a página para a inserção de uma nova gate 
##########
@app.route("/newgate")
def newFileForm():
 if(str(session['oauth_token']) == requests.get(ipuserdata + '/users/code', json = { 'ist_id' : session["istNumber"]}).json()['token']) :
    if(session["istNumber"] == 'ist1102247' ) : # Ver se é admin 
        return render_template("newGate.html")
    else: 
        return redirect(url_for('.menu'))
 else : 
        return render_template("invalidtoken.html")
    
##########
# Renderiza a página para a inserção do login de uma gate
##########

@app.route("/gates/login/")
def newFileForm2():

    return render_template('loginGate.html')


############
# Função de suporte que genera user_secret's
##############
def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


################################
#
# Dá um novo QR Code a um determinado User
# Vai buscar o user_secret e transforma-o em QRCode
# Vai pedir ao / gates / code #VER para atualizar código user_secret ( Acontece sempre que o user quiser um novo código...
# Substituindo o outro!
# Com base no novo código user_secret cria um QR code e disponibliza-o atráves de uma página
#
# ###########################################

@app.route("/gates/newqrcode")
def qrcodefunc():

 if(str(session['oauth_token']) == requests.get(ipuserdata + '/users/code', json = { 'ist_id' : session["istNumber"]}).json()['token']) :
    istid=session["istNumber"]
    # Não há json de entrada
    user= { 'ist_id' : istid }
    response = requests.post(ipuserdata + '/users/code', json= user)
    response_Json = response.json()
    user_secret = response_Json['user_secret']
    img = qrcode.make(user_secret)
    img.save(qrcodeurl)  
    img_url = url_for('static', filename='lastuserQRcode.png')
    timer = threading.Timer(30.0, timerfunction , [istid])
    timer.start()

    return render_template('giveQR.html', image_url=img_url)
 else : 
        return render_template("invalidtoken.html")


#################
# VERIFICA QR CODES
# Verfica o código user_secret do utilizador que está atualmente logado 
# Compara o código descrito com o verificado no QR Code (vem no data)
# Retorna 1 se for igual ; -1 se for diferente 
# O return é usado no java script (ScanQR) para perceber se reecaminha para uma página de sucesso ou não
#
##########

@app.route("/gates/<id>/checkcode", methods=['POST'])
def UserCheckX(id): 

    if request.method == 'POST' :
        data = request.get_json()
        response = requests.get(ipuserdata + '/users/checkcode', json= data)
        try:
            response_Json = response.json()
        except:
            print('Erro')
            data = { "id" : -1}
            return data


        userid=response_Json['id']

        if (response_Json['code'] == 1) :

            data = { "id" : userid}
            return data
        else :
            print('Erro')
            data = { "id" : -1}
            return data
 #else : 
 #       return render_template("invalidtoken.html")

#############
# Apenas uma página para representar que a porta foi aberta #VER
###########
# Redirect URL = :8000 = Estavamos a fazer um pedido para uma função dentro deste programa!
@app.route("/gates/<gateid>/user/<userid>/confirmed")
def confirm(gateid, userid):

        data2 = {
            'status': 1,
            'date': datetime.now().strftime("%d/%m/%Y %H:%M:%S"), # dd/mm/YY H:M:S
            'gate_id': gateid
        }
        
        # Atualizar o Gate Numb (Quantididades de vezes que a gate foi usada)
        try:
            response = requests.put(ipgatedata + '/gates/'+gateid+'/numb')
        except :
            print('GateData 1 Desligada!')
        try:    
            response = requests.put(ipgatedatareplica + '/gates/'+gateid+'/numb')
        except:
            print('GateData 2 Desligada!')
    
        response = requests.post(
        redirectURL +'/gatestats', 
        json = data2
        )

        UserStats = {
            'date': datetime.now().strftime("%d/%m/%Y %H:%M:%S"), # dd/mm/YY H:M:S
            'gate_id': gateid
        }
        response = requests.post(
            redirectURL + '/user/'+userid+ '/stats', 
            json = UserStats
        )

 
        return render_template('usercodegood.html', gif_url = url_for('static', filename='image1.gif') , gif2_url = url_for('static', filename='image2.gif') )





@app.route("/gates/<id>/user/notconfirmed")
def notconfirm(id):



        data2 = {
            'status': 0,
            'date': datetime.now().strftime("%d/%m/%Y %H:%M:%S"), # dd/mm/YY H:M:S
            'gate_id': id
        }
        response = requests.post(
            redirectURL +'/gatestats', 
            json = data2
        )
        return render_template('usercodebad.html')



###########
#
# Dá os stats das gates
# 
###########

@app.route("/gatestats", methods=['GET', 'POST'])
def IncrementStats(): 

    if request.method == 'POST' :
        # Não têm Json de entrada 
        
        status = request.json['status']
        date = request.json['date']
        gate_id = request.json['gate_id']
        tojson={ 
            "status" : status,
            "date" : date,
            "gate_id" : gate_id
        }
        try:
         response = requests.post(
            ipgatedata + '/gatestats', 
            json = tojson
         )
        except:
            print('Base de dados 1 desligada')
        try: 
         response = requests.post(
            ipgatedatareplica + '/gatestats', 
            json = tojson
         )
        except:
            print('Base de dados 2 desligada')

        return jsonify(tojson)
        
    #List gatesStats
    if(str(session['oauth_token']) == requests.get(ipuserdata + '/users/code', json = { 'ist_id' : session["istNumber"]}).json()['token']) :
     if(session["istNumber"] == 'ist1102247' ) :
        if request.method == 'GET':
            # Não têm Json de entrada

            try:
                response = requests.get(ipgatedata + '/gatestats')
            except:
                response = requests.get(ipgatedatareplica + '/gatestats')

            response_Json = response.json()
            return render_template(
                "gateStats.html",
                data = response_Json
            )
     else:
        return redirect(url_for('.menu'))
    else : 
       return render_template("invalidtoken.html")
        

###########
#
#
#
###########

@app.route("/user/stats", methods=['GET'])
def GoToUserStats(): 
 if(str(session['oauth_token']) == requests.get(ipuserdata + '/users/code', json = { 'ist_id' : session["istNumber"]}).json()['token']) :
    ist_id = session['istNumber']
    #List gatesStats
    if request.method == 'GET':
        # Não têm Json de entrada
        toJson = {
            'id': ist_id
        }
        response = requests.get(ipuserdata + '/user/' + ist_id + '/stats', json = toJson)

        response_Json = response.json()
        return render_template(
           "userStats.html",
           data = response_Json
        )
 else : 
        return render_template("invalidtoken.html")


###########
#
# Dá os Stats dos users
# 
###########

@app.route("/user/<id>/stats", methods=['GET', 'POST'])
def UserStats(id): 

    if request.method == 'POST' :
        # Não têm Json de entrada 
        date = request.json['date']
        gate_id = request.json['gate_id']
        tojson={ 
            "ist_id": id,
            "date" : date,
            "gate_id" : gate_id
        }
        response = requests.post(
            ipuserdata + '/user/' + id + '/stats', 
            json = tojson
        )


        return jsonify(tojson)

################
# VERFICA OS CÓDIGOS DA GATE
# Durante o login da gate, é verificado com base no ID, se o secret está correto (coloquei a location e pode-se tirar é inutil) #VER
# É uma das componentes da 1.2 Gate_web_App 
# -> The JavaScript after decoding a QRCde will invoke a suitable web-service that will verify it. (Fizemos depois) #VER
##############

@app.route("/gates/login/confirm", methods=['POST'])

def CheckGateIdAndSecret():

    if request.method != 'POST':

        print('Metodo errado de acesso ')
        abort(401)
    
    req = request.form 
    new_id= str(req.get('id'))
    new_gate_location = req.get('gate_location')
    new_gate_secret = req.get('gate_secret')

    if((isinstance(new_gate_location, str)) and (isinstance(new_gate_secret , str)) and ((' ' in new_gate_secret ) == False)) :

        try: 
            response = requests.get(ipgatedata+ '/gates/code', json = {"id" : new_id })
        except:
            response = requests.get(ipgatedatareplica+ '/gates/code', json = {"id" : new_id })

        response_Json = response.json()
        db_secret = response_Json['gate_secret']

        if new_gate_secret == db_secret:

            # Criar aqui a lógica da gate stats 
            return render_template('ScanQR.html' , message = str(new_id))
        else:
            return render_template("usercodebad.html")
    else :
        print('Erro 400 no CheckIdAndSecret')
        abort(400)

#####################
# Criar uma gate e receber a lista de todas as Gates (POST e GET)
########################

@app.route("/gates", methods=['GET','POST'])
def PostGates():
 if(str(session['oauth_token']) == requests.get(ipuserdata + '/users/code', json = { 'ist_id' : session["istNumber"]}).json()['token']) :
  if(session["istNumber"] == 'ist1102247' ) :
    if request.method == 'POST':  

         # tem Json de entrada
        req = request.form 
        new_gate_location = req.get('gate_location')
        new_gate_secret = req.get('gate_secret')
        if((isinstance(new_gate_location, str)) and (isinstance(new_gate_secret , str)) and ((' ' in new_gate_secret ) == False)) :

            try :
                response = requests.post(ipgatedata+ '/gates', json = {"gate_location" : new_gate_location , "gate_secret" : new_gate_secret})
            except :
                print('GateData 1 Desligada!')
            try : 
                response = requests.post(ipgatedatareplica+ '/gates', json = {"gate_location" : new_gate_location , "gate_secret" : new_gate_secret})
            except :
                print('GateData 2 Desligada!')
            response_Json = response.json()
            # Pode-se fazer uma confirmação de receção - não há neste momento
            return render_template('gatecreated.html')
        else : 
            print('Gate information is in the wrong format')
            return render_template('gatecodebad.html')
            
    #List gates
    if request.method == 'GET':
        # Não têm Json de entrada

        try:
            response = requests.get(ipgatedata + '/gates')
        except:
            response = requests.get(ipgatedatareplica + '/gates')

        response_Json = response.json()
        return render_template(
           "listGates.html",
           data = response_Json
        )
  else :
    return redirect(url_for('.menu'))
 else : 
        return render_template("invalidtoken.html")

@app.route("/users", methods=['GET','POST'])
def PostUsers():
 if(str(session['oauth_token']) == requests.get(ipuserdata + '/users/code', json = { 'ist_id' : session["istNumber"]}).json()['token']) :
  if(session["istNumber"] == 'ist1102247' ) :
    if request.method == 'POST':  
        print('É tudo realizado diretamete na base de dados com o POSTMAN ou com uma app que o faça , mas pode-se criar aqui um endpoint para fazer automaticamente')

    if request.method == 'GET':
    # Não tem Json de entrada
        response = requests.get(ipuserdata + '/users')
        response_Json = response.json()
        return jsonify(response_Json) 
  else : 
    return redirect(url_for('.menu'))
 else : 
        return render_template("invalidtoken.html")
    

@app.route("/oneusers/<id>", methods=['GET'])
def OneUsers(id):

    if request.method == 'GET':
    # Não tem Json de entrada
        response = requests.get(ipuserdata + '/oneusers/' + id)
        response_Json = response.json()
        return jsonify(response_Json) 


if __name__ == "__main__":
    # This allows us to use a plain HTTP callback
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = "1"

    app.secret_key = os.urandom(24)
    app.run(host='0.0.0.0', port=8000, debug=True)