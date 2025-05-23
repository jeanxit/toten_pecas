# config.py
# Apenas configurações, sem conectar ao banco aqui
mysql_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'jean',
    'database': 'Jean_Erick',
    'connection_timeout': 3600,
    'auth_plugin': 'mysql_native_password'   # <-- adicionado para forçar plugin compatível
}


# # Configurações do Firebase
# firebase_config = {
#     "apiKey": "AIzaSyByPza_xXLNCJSH1yEAWXPfZItCdCYlDPs",
#     "authDomain": "teste-181b9.firebaseapp.com",
#     "databaseURL": "https://teste-181b9-default-rtdb.firebaseio.com",
#     "projectId": "teste-181b9",
#     "storageBucket": "teste-181b9.appspot.com",
#     "messagingSenderId": "950036297761",
#     "appId": "1:950036297761:web:56791d5d8435ea83ea8b60"
# }

# # Inicialização
# firebase = pyrebase.initialize_app(firebase_config)
# db = firebase.database()

# # Pega os dados do nó "mensagens"
# mensagens = db.child("mensagens").get()

# # Verificação de existência de dados
# if mensagens.each():
#     for item in mensagens.each():
#         print(item.key(), item.val())
# else:
#     print("⚠️ Nenhuma mensagem encontrada no Firebase.")
